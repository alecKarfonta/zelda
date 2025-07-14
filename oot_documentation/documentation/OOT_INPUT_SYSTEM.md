# OOT Input System Deep Dive

## Overview

This document provides a comprehensive analysis of the Input System in The Legend of Zelda: Ocarina of Time (OOT) based on examination of the actual decomp source code. The input system is responsible for processing controller input, managing multiple controllers, providing input abstraction layers, and integrating with various gameplay systems including the player, camera, and UI systems.

## Architecture Overview

### Input System Components

The input system is built with several key components working together:

**Core Components:**
- **PadMgr**: Low-level controller management and polling
- **Input Structure**: High-level input abstraction and state management
- **Controller Interface**: Hardware abstraction for different controller types
- **Input Processing**: Frame-based input state calculations
- **Ocarina System**: Special input processing for ocarina gameplay
- **Rumble Management**: Force feedback control

### Input Structure

**Input Structure Definition:**
```c
typedef struct {
    /* 0x00 */ OSContPad cur;
    /* 0x06 */ OSContPad prev;
    /* 0x0C */ OSContPad press; // input pressed this frame
    /* 0x12 */ OSContPad rel;   // input released this frame
} Input; // size = 0x18
```

**OSContPad Structure:**
```c
typedef struct {
    /* 0x00 */ u16 button;
    /* 0x02 */ s8  stick_x;
    /* 0x03 */ s8  stick_y;
    /* 0x04 */ u8  errno;
} OSContPad;
```

## PadMgr - Controller Management

### PadMgr Initialization and Threading

**PadMgr Thread Entry (`padmgr.c:511`):**
```c
void PadMgr_ThreadEntry(PadMgr* padMgr) {
    s16* msg = NULL;
    s32 exit;

    PRINTF(T("コントローラスレッド実行開始\n", "Controller thread execution start"));

    exit = false;
    while (!exit) {
        if (gPadMgrLogSeverity >= LOG_SEVERITY_VERBOSE && MQ_IS_EMPTY(&padMgr->interruptQueue)) {
            PRINTF(T("コントローラスレッドイベント待ち %lld\n", "Waiting for controller thread event %lld\n"),
                   OS_CYCLES_TO_USEC(osGetTime()));
        }

        osRecvMesg(&padMgr->interruptQueue, (OSMesg*)&msg, OS_MESG_BLOCK);
        LOG_UTILS_CHECK_NULL_POINTER("msg", msg, "../padmgr.c", 563);

        switch (*msg) {
            case OS_SC_RETRACE_MSG:
                if (gPadMgrLogSeverity >= LOG_SEVERITY_VERBOSE) {
                    PRINTF("padmgr_HandleRetraceMsg START %lld\n", OS_CYCLES_TO_USEC(osGetTime()));
                }

                PadMgr_HandleRetrace(padMgr);

                if (gPadMgrLogSeverity >= LOG_SEVERITY_VERBOSE) {
                    PRINTF("padmgr_HandleRetraceMsg END   %lld\n", OS_CYCLES_TO_USEC(osGetTime()));
                }
                break;
            case OS_SC_PRE_NMI_MSG:
                PadMgr_HandlePreNMI(padMgr);
                break;
            case OS_SC_NMI_MSG:
                exit = true;
                break;
        }
    }

    IrqMgr_RemoveClient(padMgr->irqMgr, &padMgr->irqClient);

    PRINTF(T("コントローラスレッド実行終了\n", "Controller thread execution end\n"));
}
```

### Controller Polling and Processing

**Retrace Handler (`padmgr.c:449`):**
```c
void PadMgr_HandleRetrace(PadMgr* padMgr) {
    OSMesgQueue* serialEventQueue = PadMgr_AcquireSerialEventQueue(padMgr);

    // Begin reading controller data
    osContStartReadData(serialEventQueue);

    // Execute retrace callback
    if (padMgr->retraceCallback != NULL) {
        padMgr->retraceCallback(padMgr, padMgr->retraceCallbackArg);
    }

    // Wait for controller data
    osRecvMesg(serialEventQueue, NULL, OS_MESG_BLOCK);
    osContGetReadData(padMgr->pads);

#if !DEBUG_FEATURES
    // Clear controllers 2 and 4
    bzero(&padMgr->pads[1], sizeof(OSContPad));
    bzero(&padMgr->pads[3], sizeof(OSContPad));
#endif

    // If resetting, clear all controllers
    if (padMgr->isResetting) {
        bzero(padMgr->pads, sizeof(padMgr->pads));
    }

    // Update input data
    PadMgr_UpdateInputs(padMgr);

    // Query controller status for all controllers
    osContStartQuery(serialEventQueue);
    osRecvMesg(serialEventQueue, NULL, OS_MESG_BLOCK);
    osContGetQuery(padMgr->padStatus);

    PadMgr_ReleaseSerialEventQueue(padMgr, serialEventQueue);

    {
        u32 mask = 0;
        s32 i;

        // Update the state of connected controllers
        for (i = 0; i < MAXCONTROLLERS; i++) {
            if (padMgr->padStatus[i].errno == 0) {
                // Only standard N64 controllers are supported
                if (padMgr->padStatus[i].type == CONT_TYPE_NORMAL) {
                    mask |= 1 << i;
                } else {
                    LOG_HEX("this->pad_status[i].type", padMgr->padStatus[i].type, "../padmgr.c", 458);
                    PRINTF(T("知らない種類のコントローラが接続されています\n",
                             "An unknown type of controller is connected\n"));
                }
            }
        }
        padMgr->validCtrlrsMask = mask;
    }

    if (FAULT_MSG_ID != 0) {
        // If fault is active, no rumble
        PadMgr_RumbleStop(padMgr);
    } else if (padMgr->rumbleOffTimer > 0) {
        // If the rumble off timer is active, no rumble
        --padMgr->rumbleOffTimer;
        PadMgr_RumbleStop(padMgr);
    } else if (padMgr->rumbleOnTimer == 0) {
        // If the rumble on timer is inactive, no rumble
        PadMgr_RumbleStop(padMgr);
    } else if (!padMgr->isResetting) {
        // If not resetting, update rumble
        PadMgr_UpdateRumble(padMgr);
        --padMgr->rumbleOnTimer;
    }
}
```

### Input State Processing

**Input Update Function (`padmgr.c:291`):**
```c
void PadMgr_UpdateInputs(PadMgr* padMgr) {
    s32 i;
    Input* input;
    OSContPad* pad; // original name: "padnow1"
    s32 buttonDiff;

    PadMgr_LockPadData(padMgr);

    for (input = &padMgr->inputs[0], pad = &padMgr->pads[0], i = 0; i < padMgr->nControllers; i++, input++, pad++) {
        input->prev = input->cur;

        switch (pad->errno) {
            case 0:
                // No error, copy inputs
                input->cur = *pad;
                if (!padMgr->ctrlrIsConnected[i]) {
                    padMgr->ctrlrIsConnected[i] = true;
                    PADMGR_LOG(i, T("認識しました", "Recognized"));
                }
                break;
            case (CHNL_ERR_OVERRUN >> 4):
                // Overrun error, reuse previous inputs
                input->cur = input->prev;
                LOG_NUM("this->Key_switch[i]", padMgr->ctrlrIsConnected[i], "../padmgr.c", 380);
                PADMGR_LOG(i, T("オーバーランエラーが発生", "Overrun error occurred"));
                break;
            case (CHNL_ERR_NORESP >> 4):
                // No response error, take inputs as 0
                input->cur.button = 0;
                input->cur.stick_x = 0;
                input->cur.stick_y = 0;
                input->cur.errno = pad->errno;
                if (padMgr->ctrlrIsConnected[i]) {
                    // If we get no response, consider the controller disconnected
                    padMgr->ctrlrIsConnected[i] = false;
                    padMgr->pakType[i] = CONT_PAK_NONE;
                    padMgr->rumbleTimer[i] = UINT8_MAX;
                    PADMGR_LOG(i, T("応答しません", "Not responding"));
                }
                break;
            default:
                // Unknown error response
                LOG_HEX("padnow1->errno", pad->errno, "../padmgr.c", 396);
                Fault_AddHungupAndCrash("../padmgr.c", LN3(379, 382, 397, 397));
                break;
        }

        // Calculate pressed and relative inputs
        buttonDiff = input->prev.button ^ input->cur.button;
        input->press.button |= (u16)(buttonDiff & input->cur.button);
        input->rel.button |= (u16)(buttonDiff & input->prev.button);
        PadUtils_UpdateRelXY(input);
        input->press.stick_x += (s8)(input->cur.stick_x - input->prev.stick_x);
        input->press.stick_y += (s8)(input->cur.stick_y - input->prev.stick_y);
    }

    PadMgr_UnlockPadData(padMgr);
}
```

### Input Data Access

**Input Data Request (`padmgr.c:503`):**
```c
void PadMgr_RequestPadData(PadMgr* padMgr, Input* inputs, s32 gameRequest) {
    s32 i;
    Input* inputIn;
    Input* inputOut;
    s32 buttonDiff;

    PadMgr_LockPadData(padMgr);

    for (inputIn = &padMgr->inputs[0], inputOut = &inputs[0], i = 0; i < MAXCONTROLLERS; i++, inputIn++, inputOut++) {
        if (gameRequest) {
            // Copy inputs as-is, press and rel are calculated prior in `PadMgr_UpdateInputs`
            *inputOut = *inputIn;
            // Zero parts of the press and rel inputs in the polled inputs so they are not read more than once
            inputIn->press.button = 0;
            inputIn->press.stick_x = 0;
            inputIn->press.stick_y = 0;
            inputIn->rel.button = 0;
        } else {
            // Take as the previous inputs the inputs that are currently in the destination array
            inputOut->prev = inputOut->cur;
            // Copy current inputs from the polled inputs
            inputOut->cur = inputIn->cur;
            // Calculate press and rel from these
            buttonDiff = inputOut->prev.button ^ inputOut->cur.button;
            inputOut->press.button = inputOut->cur.button & buttonDiff;
            inputOut->rel.button = inputOut->prev.button & buttonDiff;
            PadUtils_UpdateRelXY(inputOut);
            inputOut->press.stick_x += (s8)(inputOut->cur.stick_x - inputOut->prev.stick_x);
            inputOut->press.stick_y += (s8)(inputOut->cur.stick_y - inputOut->prev.stick_y);
        }
    }

    PadMgr_UnlockPadData(padMgr);
}
```

## Input Utilities

### Basic Input Utilities

**Input Utility Functions (`z_libu64_pad.c:3`):**
```c
void PadUtils_Init(Input* input) {
    bzero(input, sizeof(Input));
}

void PadUtils_ResetPressRel(Input* input) {
    input->press.button = 0;
#if PLATFORM_N64
    input->press.stick_x = 0;
    input->press.stick_y = 0;
#endif
    input->rel.button = 0;
}

u32 PadUtils_CheckCurExact(Input* input, u16 value) {
    return value == input->cur.button;
}

u32 PadUtils_CheckCur(Input* input, u16 key) {
    return key == (input->cur.button & key);
}

u32 PadUtils_CheckPressed(Input* input, u16 key) {
    return key == (input->press.button & key);
}

u32 PadUtils_CheckReleased(Input* input, u16 key) {
    return key == (input->rel.button & key);
}
```

### Analog Stick Processing

**Analog Stick Utilities:**
```c
s8 PadUtils_GetCurX(Input* input) {
    return input->cur.stick_x;
}

s8 PadUtils_GetCurY(Input* input) {
    return input->cur.stick_y;
}

void PadUtils_SetRelXY(Input* input, s32 x, s32 y) {
    input->rel.stick_x = x;
    input->rel.stick_y = y;
}

s8 PadUtils_GetRelX(Input* input) {
    return input->rel.stick_x;
}

s8 PadUtils_GetRelY(Input* input) {
    return input->rel.stick_y;
}

#if PLATFORM_N64
s8 PadUtils_GetPressX(Input* input) {
    return input->press.stick_x;
}

s8 PadUtils_GetPressY(Input* input) {
    return input->press.stick_y;
}
#endif
```

## Player Input Integration

### Player Control Processing

**Player Control Stick Processing (`z_player.c:2210`):**
```c
void Player_ProcessControlStick(PlayState* play, Player* this) {
    s8 spinAngle;
    s8 direction;

    this->prevControlStickMagnitude = sControlStickMagnitude;
    this->prevControlStickAngle = sControlStickAngle;

    Lib_GetControlStickData(&sControlStickMagnitude, &sControlStickAngle, sControlInput);

    sControlStickWorldYaw = Camera_GetInputDirYaw(GET_ACTIVE_CAM(play)) + sControlStickAngle;

    this->controlStickDataIndex = (this->controlStickDataIndex + 1) % 4;

    if (sControlStickMagnitude < 55.0f) {
        direction = PLAYER_STICK_DIR_NONE;
        spinAngle = -1;
    } else {
        spinAngle = (u16)(sControlStickAngle + 0x2000) >> 9;
        direction = (u16)((s16)(sControlStickWorldYaw - this->actor.shape.rot.y) + 0x2000) >> 14;
    }

    this->controlStickSpinAngles[this->controlStickDataIndex] = spinAngle;
    this->controlStickDirections[this->controlStickDataIndex] = direction;
}
```

### Player Movement Input

**Player Movement Calculation (`z_player.c:4050`):**
```c
s32 Player_CalcSpeedAndYawFromControlStick(PlayState* play, Player* this, f32* outSpeedTarget, s16* outYawTarget,
                                           f32 speedMode) {
    f32 temp;
    f32 sinFloorPitch;
    f32 floorPitchInfluence;
    f32 speedCap;

    if ((this->unk_6AD != 0) || (play->transitionTrigger == TRANS_TRIGGER_START) ||
        (this->stateFlags1 & PLAYER_STATE1_0)) {
        *outSpeedTarget = 0.0f;
        *outYawTarget = this->actor.shape.rot.y;
    } else {
        *outSpeedTarget = sControlStickMagnitude;
        *outYawTarget = sControlStickAngle;

        // The value of `speedMode` is never actually used. It only toggles this condition.
        // See the definition of `SPEED_MODE_LINEAR` and `SPEED_MODE_CURVED` for more information.
        if (speedMode != SPEED_MODE_LINEAR) {
            *outSpeedTarget -= 20.0f;

            if (*outSpeedTarget < 0.0f) {
                // If control stick magnitude is below 20, return zero speed.
                *outSpeedTarget = 0.0f;
            } else {
                // Cosine of the control stick magnitude isn't exactly meaningful, but
                // it happens to give a desirable curve for grounded movement speed relative
                // to control stick magnitude.
                temp = 1.0f - Math_CosS(*outSpeedTarget * 450.0f);
                *outSpeedTarget = (SQ(temp) * 30.0f) + 7.0f;
            }
        } else {
            // Speed increases linearly relative to control stick magnitude
            *outSpeedTarget *= 0.8f;
        }

        if (sControlStickMagnitude != 0.0f) {
            sinFloorPitch = Math_SinS(this->floorPitch);
            speedCap = this->unk_880;
            floorPitchInfluence = CLAMP(sinFloorPitch, 0.0f, 0.6f);

            if (this->unk_6C4 != 0.0f) {
                speedCap -= this->unk_6C4 * 0.008f;
                speedCap = CLAMP_MIN(speedCap, 2.0f);
            }

            *outSpeedTarget = (*outSpeedTarget * 0.14f) - (8.0f * floorPitchInfluence * floorPitchInfluence);
            *outSpeedTarget = CLAMP(*outSpeedTarget, 0.0f, speedCap);

            return true;
        }
    }

    return false;
}
```

### Player Common Input Processing

**Player Common Update (`z_player.c:11669`):**
```c
void Player_UpdateCommon(Player* this, PlayState* play, Input* input) {
    s32 pad;

    sControlInput = input;

    if (this->unk_A86 < 0) {
        this->unk_A86++;
        if (this->unk_A86 == 0) {
            this->unk_A86 = 1;
            Sfx_PlaySfxCentered(NA_SE_OC_REVENGE);
        }
    }

    Math_Vec3f_Copy(&this->actor.prevPos, &this->actor.home.pos);

    if (this->unk_A73 != 0) {
        this->unk_A73--;
    }

    if (this->textboxBtnCooldownTimer != 0) {
        this->textboxBtnCooldownTimer--;
    }

    if (this->unk_A87 != 0) {
        this->unk_A87--;
    }

    if (this->invincibilityTimer < 0) {
        this->invincibilityTimer++;
    } else if (this->invincibilityTimer > 0) {
        this->invincibilityTimer--;
    }

    if (this->unk_890 != 0) {
        this->unk_890--;
    }

    Player_UpdateInterface(play, this);

    Player_UpdateZTargeting(this, play);

    if ((this->heldItemAction == PLAYER_IA_DEKU_STICK) && (this->unk_860 != 0)) {
        Player_UpdateBurningDekuStick(play, this);
    } else if ((this->heldItemAction == PLAYER_IA_FISHING_POLE) && (this->unk_860 < 0)) {
        this->unk_860++;
    }

    if (this->bodyShockTimer != 0) {
        Player_UpdateBodyShock(play, this);
    }

    if (this->bodyIsBurning) {
        Player_UpdateBodyBurn(play, this);
    }

    // ... more input processing
}
```

## Ocarina Input System

### Ocarina Input Processing

**Ocarina Controller Input (`general.c:1281`):**
```c
void AudioOcarina_ReadControllerInput(void) {
    Input inputs[MAXCONTROLLERS];
    Input* input = &inputs[0];
    u32 ocarinaInputButtonPrev = sOcarinaInputButtonCur;

    PadMgr_RequestPadData(&gPadMgr, inputs, false);
    sOcarinaInputButtonCur = input->cur.button;
    sOcarinaInputButtonPrev = ocarinaInputButtonPrev;
    sOcarinaInputStickAdj.x = input->rel.stick_x;
    sOcarinaInputStickAdj.y = input->rel.stick_y;
}
```

### Ocarina Button Mapping

**Ocarina Button Configuration (`general.c:1244`):**
```c
#if PLATFORM_N64

#define OCARINA_ALLOWED_BUTTON_MASK (BTN_A | BTN_CUP | BTN_CDOWN | BTN_CLEFT | BTN_CRIGHT)
#define OCARINA_A_MAP BTN_A
#define OCARINA_CUP_MAP BTN_CUP
#define OCARINA_CDOWN_MAP BTN_CDOWN

#else

#define OCARINA_ALLOWED_BUTTON_MASK sOcarinaAllowedButtonMask
#define OCARINA_A_MAP sOcarinaAButtonMap
#define OCARINA_CUP_MAP sOcarinaCUpButtonMap
#define OCARINA_CDOWN_MAP sOcarinaCDownButtonMap

void AudioOcarina_SetCustomButtonMapping(u8 useCustom) {
    if (!useCustom) {
        AUDIO_PRINTF("AUDIO : Ocarina Control Assign Normal\n");
        OCARINA_ALLOWED_BUTTON_MASK = (BTN_A | BTN_CUP | BTN_CDOWN | BTN_CLEFT | BTN_CRIGHT);
        OCARINA_A_MAP = BTN_A;
        OCARINA_CUP_MAP = BTN_CUP;
        OCARINA_CDOWN_MAP = BTN_CDOWN;
    } else {
        AUDIO_PRINTF("AUDIO : Ocarina Control Assign Custom\n");
        OCARINA_ALLOWED_BUTTON_MASK = (BTN_A | BTN_B | BTN_CDOWN | BTN_CLEFT | BTN_CRIGHT);
        OCARINA_A_MAP = BTN_B;
        OCARINA_CUP_MAP = BTN_CDOWN;
        OCARINA_CDOWN_MAP = BTN_A;
    }
}

#endif
```

### Ocarina Playback Control

**Ocarina Play Controller Input (`general.c:1638`):**
```c
void AudioOcarina_PlayControllerInput(u8 unused) {
    u32 ocarinaBtnsHeld;

    // Prevents two different ocarina notes from being played on two consecutive frames
    if ((sOcarinaFlags != 0) && (sOcarinaDropInputTimer != 0)) {
        sOcarinaDropInputTimer--;
        return;
    }

    // Ensures the button pressed to start the ocarina does not also play an ocarina note
    if ((sOcarinaInputButtonStart == 0) || ((sOcarinaInputButtonStart & OCARINA_ALLOWED_BUTTON_MASK) !=
                                            (sOcarinaInputButtonCur & OCARINA_ALLOWED_BUTTON_MASK))) {
        sOcarinaInputButtonStart = 0;
        if (1) {}
        sCurOcarinaPitch = OCARINA_PITCH_NONE;
        sCurOcarinaButtonIndex = OCARINA_BTN_INVALID;
        ocarinaBtnsHeld = (sOcarinaInputButtonCur & OCARINA_ALLOWED_BUTTON_MASK) &
                          (sOcarinaInputButtonPrev & OCARINA_ALLOWED_BUTTON_MASK);
        if (!(sOcarinaInputButtonPress & ocarinaBtnsHeld) && (sOcarinaInputButtonCur != 0)) {
            sOcarinaInputButtonPress = sOcarinaInputButtonCur;
        } else {
            sOcarinaInputButtonPress &= ocarinaBtnsHeld;
        }

        // Interprets and transforms controller input into ocarina buttons and notes
        // ... more processing
    }
}
```

## Frame Advance System

### Frame Advance Implementation

**Frame Advance Input Processing (`z_frame_advance.c:20`):**
```c
s32 FrameAdvance_Update(FrameAdvanceContext* frameAdvCtx, Input* input) {
    if (CHECK_BTN_ALL(input->cur.button, BTN_R) && CHECK_BTN_ALL(input->press.button, BTN_DDOWN)) {
        frameAdvCtx->enabled = !frameAdvCtx->enabled;
    }

    if (!frameAdvCtx->enabled || (CHECK_BTN_ALL(input->cur.button, BTN_Z) &&
                                  (CHECK_BTN_ALL(input->press.button, BTN_R) ||
                                   (CHECK_BTN_ALL(input->cur.button, BTN_R) && (++frameAdvCtx->timer >= 9))))) {
        frameAdvCtx->timer = 0;
        return true;
    }

    return false;
}
```

## UI Input Integration

### Shop Interface Input

**Shop Joystick Input (`z_en_ossan.c:771`):**
```c
void EnOssan_UpdateJoystickInputState(PlayState* play, EnOssan* this) {
    Input* input = &play->state.input[0];
    s8 stickX = input->rel.stick_x;
    s8 stickY = input->rel.stick_y;

    this->moveHorizontal = this->moveVertical = false;

    if (this->stickAccumX == 0) {
        if (stickX > 30 || stickX < -30) {
            this->stickAccumX = stickX;
            this->moveHorizontal = true;
        }
    } else if (stickX <= 30 && stickX >= -30) {
        this->stickAccumX = 0;
    } else if (this->stickAccumX * stickX < 0) { // Stick has swapped directions
        this->stickAccumX = stickX;
        this->moveHorizontal = true;
    } else {
        this->stickAccumX += stickX;

        if (this->stickAccumX > 2000) {
            this->stickAccumX = 2000;
        } else if (this->stickAccumX < -2000) {
            this->stickAccumX = -2000;
        }
    }

    if (this->stickAccumY == 0) {
        if (stickY > 30 || stickY < -30) {
            this->stickAccumY = stickY;
            this->moveVertical = true;
        }
    } else if (stickY <= 30 && stickY >= -30) {
        this->stickAccumY = 0;
    } else if (this->stickAccumY * stickY < 0) { // Stick has swapped directions
        this->stickAccumY = stickY;
        this->moveVertical = true;
    } else {
        this->stickAccumY += stickY;

        if (this->stickAccumY > 2000) {
            this->stickAccumY = 2000;
        } else if (this->stickAccumY < -2000) {
            this->stickAccumY = -2000;
        }
    }
}
```

## Debug Input System

### Debug Input Processing

**Debug Input Handling (`game.c:98`):**
```c
void func_800C4344(GameState* gameState) {
#if DEBUG_FEATURES
    Input* selectedInput;
    s32 hexDumpSize;
    u16 inputCompareValue;

    if (R_HREG_MODE == HREG_MODE_INPUT_TEST) {
        selectedInput =
            &gameState->input[(u32)R_INPUT_TEST_CONTROLLER_PORT < MAXCONTROLLERS ? R_INPUT_TEST_CONTROLLER_PORT : 0];

        inputCompareValue = R_INPUT_TEST_COMPARE_VALUE;
        R_INPUT_TEST_BUTTON_CUR = selectedInput->cur.button;
        R_INPUT_TEST_BUTTON_PRESS = selectedInput->press.button;
        R_INPUT_TEST_REL_STICK_X = selectedInput->rel.stick_x;
        R_INPUT_TEST_REL_STICK_Y = selectedInput->rel.stick_y;
        R_INPUT_TEST_REL_STICK_X_2 = selectedInput->rel.stick_x;
        R_INPUT_TEST_REL_STICK_Y_2 = selectedInput->rel.stick_y;
        R_INPUT_TEST_CUR_STICK_X = selectedInput->cur.stick_x;
        R_INPUT_TEST_CUR_STICK_Y = selectedInput->cur.stick_y;
        R_INPUT_TEST_COMPARE_BUTTON_CUR = (selectedInput->cur.button == inputCompareValue);
        R_INPUT_TEST_COMPARE_COMBO_CUR = CHECK_BTN_ALL(selectedInput->cur.button, inputCompareValue);
        R_INPUT_TEST_COMPARE_COMBO_PRESS = CHECK_BTN_ALL(selectedInput->press.button, inputCompareValue);
    }

    if (gIsCtrlr2Valid) {
        Regs_UpdateEditor(&gameState->input[1]);
    }

    gDmaMgrVerbose = HREG(60);
    gDmaMgrDmaBuffSize = SREG(21) != 0 ? ALIGN16(SREG(21)) : DMAMGR_DEFAULT_BUFSIZE;
    gSystemArenaLogSeverity = HREG(61);
    gZeldaArenaLogSeverity = HREG(62);
#endif
}
```

## Rumble System

### Rumble Management

**Rumble functionality is integrated into the PadMgr system:**

```c
// Rumble timer and state management
typedef struct {
    u8 rumbleTimer[MAXCONTROLLERS];
    u8 rumbleOnTimer;
    u8 rumbleOffTimer;
    u8 pakType[MAXCONTROLLERS];
    // ... other fields
} PadMgr;
```

**Rumble Update in Retrace Handler:**
```c
if (FAULT_MSG_ID != 0) {
    // If fault is active, no rumble
    PadMgr_RumbleStop(padMgr);
} else if (padMgr->rumbleOffTimer > 0) {
    // If the rumble off timer is active, no rumble
    --padMgr->rumbleOffTimer;
    PadMgr_RumbleStop(padMgr);
} else if (padMgr->rumbleOnTimer == 0) {
    // If the rumble on timer is inactive, no rumble
    PadMgr_RumbleStop(padMgr);
} else if (!padMgr->isResetting) {
    // If not resetting, update rumble
    PadMgr_UpdateRumble(padMgr);
    --padMgr->rumbleOnTimer;
}
```

## Practical Examples

### Custom Input Handler

**Creating a Custom Input Handler:**

```c
// Custom input handler structure
typedef struct {
    Input* input;
    u32 comboBuffer[16];
    u8 comboIndex;
    u8 comboTimer;
    u8 enabled;
} CustomInputHandler;

// Initialize custom input handler
void CustomInputHandler_Init(CustomInputHandler* handler, Input* input) {
    handler->input = input;
    handler->comboIndex = 0;
    handler->comboTimer = 0;
    handler->enabled = 1;
    
    // Clear combo buffer
    for (int i = 0; i < 16; i++) {
        handler->comboBuffer[i] = 0;
    }
}

// Update custom input handler
void CustomInputHandler_Update(CustomInputHandler* handler) {
    if (!handler->enabled) return;
    
    // Check for button presses
    if (handler->input->press.button != 0) {
        // Add to combo buffer
        handler->comboBuffer[handler->comboIndex] = handler->input->press.button;
        handler->comboIndex = (handler->comboIndex + 1) % 16;
        handler->comboTimer = 60; // 1 second timeout
    }
    
    // Update combo timer
    if (handler->comboTimer > 0) {
        handler->comboTimer--;
        if (handler->comboTimer == 0) {
            // Combo timeout, clear buffer
            handler->comboIndex = 0;
            for (int i = 0; i < 16; i++) {
                handler->comboBuffer[i] = 0;
            }
        }
    }
    
    // Check for specific combo patterns
    CustomInputHandler_CheckCombos(handler);
}

// Check for combo patterns
void CustomInputHandler_CheckCombos(CustomInputHandler* handler) {
    // Example: Check for Up, Up, Down, Down, Left, Right, Left, Right, B, A
    static u32 konamiCode[] = {
        BTN_DUP, BTN_DUP, BTN_DDOWN, BTN_DDOWN,
        BTN_DLEFT, BTN_DRIGHT, BTN_DLEFT, BTN_DRIGHT,
        BTN_B, BTN_A
    };
    
    if (handler->comboIndex >= 10) {
        u8 matches = 0;
        for (int i = 0; i < 10; i++) {
            if (handler->comboBuffer[(handler->comboIndex - 10 + i) % 16] == konamiCode[i]) {
                matches++;
            }
        }
        
        if (matches == 10) {
            // Konami code detected!
            PRINTF("Konami code activated!\n");
            // Execute special functionality
        }
    }
}
```

### Input Filtering System

**Input Filtering for Smooth Movement:**

```c
// Input filter structure
typedef struct {
    f32 deadzone;
    f32 sensitivity;
    f32 acceleration;
    f32 prevMagnitude;
    s16 prevAngle;
    u8 filterEnabled;
} InputFilter;

// Initialize input filter
void InputFilter_Init(InputFilter* filter, f32 deadzone, f32 sensitivity, f32 acceleration) {
    filter->deadzone = deadzone;
    filter->sensitivity = sensitivity;
    filter->acceleration = acceleration;
    filter->prevMagnitude = 0.0f;
    filter->prevAngle = 0;
    filter->filterEnabled = 1;
}

// Apply input filter
void InputFilter_Apply(InputFilter* filter, Input* input, f32* outMagnitude, s16* outAngle) {
    if (!filter->filterEnabled) {
        Lib_GetControlStickData(outMagnitude, outAngle, input);
        return;
    }
    
    // Get raw input
    f32 rawMagnitude;
    s16 rawAngle;
    Lib_GetControlStickData(&rawMagnitude, &rawAngle, input);
    
    // Apply deadzone
    if (rawMagnitude < filter->deadzone) {
        *outMagnitude = 0.0f;
        *outAngle = filter->prevAngle;
        return;
    }
    
    // Normalize magnitude beyond deadzone
    f32 normalizedMagnitude = (rawMagnitude - filter->deadzone) / (1.0f - filter->deadzone);
    
    // Apply sensitivity curve
    normalizedMagnitude = powf(normalizedMagnitude, filter->sensitivity);
    
    // Apply acceleration smoothing
    f32 targetMagnitude = normalizedMagnitude;
    f32 magnitudeDelta = targetMagnitude - filter->prevMagnitude;
    f32 maxChange = filter->acceleration;
    
    if (fabsf(magnitudeDelta) > maxChange) {
        targetMagnitude = filter->prevMagnitude + (magnitudeDelta > 0 ? maxChange : -maxChange);
    }
    
    // Output filtered values
    *outMagnitude = targetMagnitude;
    *outAngle = rawAngle;
    
    // Store for next frame
    filter->prevMagnitude = targetMagnitude;
    filter->prevAngle = rawAngle;
}
```

### Multi-Controller Support

**Multi-Controller Input Management:**

```c
// Multi-controller manager
typedef struct {
    Input inputs[MAXCONTROLLERS];
    u8 controllerAssignments[MAXCONTROLLERS];
    u8 activeControllers;
    u8 primaryController;
} MultiControllerManager;

// Initialize multi-controller manager
void MultiController_Init(MultiControllerManager* manager) {
    manager->activeControllers = 0;
    manager->primaryController = 0;
    
    for (int i = 0; i < MAXCONTROLLERS; i++) {
        PadUtils_Init(&manager->inputs[i]);
        manager->controllerAssignments[i] = 0xFF; // Unassigned
    }
}

// Update multi-controller manager
void MultiController_Update(MultiControllerManager* manager) {
    // Request input data from PadMgr
    PadMgr_RequestPadData(&gPadMgr, manager->inputs, true);
    
    // Update active controller mask
    manager->activeControllers = 0;
    for (int i = 0; i < MAXCONTROLLERS; i++) {
        if (manager->inputs[i].cur.button != 0 || 
            manager->inputs[i].cur.stick_x != 0 || 
            manager->inputs[i].cur.stick_y != 0) {
            manager->activeControllers |= (1 << i);
        }
    }
    
    // Auto-assign primary controller
    if (manager->primaryController >= MAXCONTROLLERS || 
        !(manager->activeControllers & (1 << manager->primaryController))) {
        // Find first active controller
        for (int i = 0; i < MAXCONTROLLERS; i++) {
            if (manager->activeControllers & (1 << i)) {
                manager->primaryController = i;
                break;
            }
        }
    }
}

// Get primary controller input
Input* MultiController_GetPrimaryInput(MultiControllerManager* manager) {
    if (manager->primaryController < MAXCONTROLLERS) {
        return &manager->inputs[manager->primaryController];
    }
    return &manager->inputs[0]; // Fallback
}

// Check if specific controller is active
u8 MultiController_IsActive(MultiControllerManager* manager, u8 controller) {
    if (controller >= MAXCONTROLLERS) return 0;
    return (manager->activeControllers & (1 << controller)) != 0;
}
```

## Performance Optimization

### Input Polling Optimization

**Efficient Input Processing:**

```c
// Optimized input processing for performance-critical sections
typedef struct {
    u32 cachedButtons;
    f32 cachedStickMagnitude;
    s16 cachedStickAngle;
    u8 cacheValid;
} InputCache;

// Cache input data for multiple uses per frame
void InputCache_Update(InputCache* cache, Input* input) {
    cache->cachedButtons = input->cur.button;
    Lib_GetControlStickData(&cache->cachedStickMagnitude, &cache->cachedStickAngle, input);
    cache->cacheValid = 1;
}

// Get cached button state
u32 InputCache_GetButtons(InputCache* cache) {
    return cache->cachedButtons;
}

// Get cached stick data
void InputCache_GetStickData(InputCache* cache, f32* magnitude, s16* angle) {
    *magnitude = cache->cachedStickMagnitude;
    *angle = cache->cachedStickAngle;
}
```

### Input Prediction

**Input Prediction for Smooth Movement:**

```c
// Input prediction system
typedef struct {
    Input history[8];
    u8 historyIndex;
    u8 predictionEnabled;
} InputPredictor;

// Update input predictor
void InputPredictor_Update(InputPredictor* predictor, Input* input) {
    // Store input in history
    predictor->history[predictor->historyIndex] = *input;
    predictor->historyIndex = (predictor->historyIndex + 1) % 8;
}

// Predict next input state
void InputPredictor_Predict(InputPredictor* predictor, Input* predictedInput) {
    if (!predictor->predictionEnabled) {
        *predictedInput = predictor->history[(predictor->historyIndex - 1 + 8) % 8];
        return;
    }
    
    // Simple prediction based on recent input trends
    Input* recent = &predictor->history[(predictor->historyIndex - 1 + 8) % 8];
    Input* previous = &predictor->history[(predictor->historyIndex - 2 + 8) % 8];
    
    // Predict button state (keep current)
    predictedInput->cur.button = recent->cur.button;
    
    // Predict stick movement based on velocity
    s8 stickVelX = recent->cur.stick_x - previous->cur.stick_x;
    s8 stickVelY = recent->cur.stick_y - previous->cur.stick_y;
    
    predictedInput->cur.stick_x = recent->cur.stick_x + stickVelX;
    predictedInput->cur.stick_y = recent->cur.stick_y + stickVelY;
    
    // Clamp to valid range
    predictedInput->cur.stick_x = CLAMP(predictedInput->cur.stick_x, -80, 80);
    predictedInput->cur.stick_y = CLAMP(predictedInput->cur.stick_y, -80, 80);
}
```

## Error Handling and Edge Cases

### Controller Disconnection Handling

**Graceful Controller Disconnection:**

```c
// Controller disconnection detection
void HandleControllerDisconnection(PlayState* play, u8 controller) {
    if (controller >= MAXCONTROLLERS) return;
    
    // Check if this was the primary controller
    if (controller == 0) {
        // Primary controller disconnected
        PRINTF("Primary controller disconnected\n");
        
        // Pause game if in gameplay
        if (play->gameOverCtx.state == GAMEOVER_INACTIVE) {
            // Trigger pause menu or show controller disconnected message
            play->pauseCtx.state = PAUSE_STATE_OPENING;
            play->pauseCtx.debugState = PAUSE_DEBUG_CONTROLLER_DISCONNECTED;
        }
        
        // Reset player input state
        Player* player = GET_PLAYER(play);
        if (player != NULL) {
            player->stateFlags1 &= ~(PLAYER_STATE1_USING_OCARINA | PLAYER_STATE1_TALKING);
        }
    }
}

// Controller reconnection detection
void HandleControllerReconnection(PlayState* play, u8 controller) {
    if (controller >= MAXCONTROLLERS) return;
    
    PRINTF("Controller %d reconnected\n", controller);
    
    // If this was the primary controller, resume game
    if (controller == 0 && play->pauseCtx.debugState == PAUSE_DEBUG_CONTROLLER_DISCONNECTED) {
        play->pauseCtx.state = PAUSE_STATE_CLOSING;
        play->pauseCtx.debugState = PAUSE_DEBUG_NONE;
    }
}
```

### Input Validation

**Input Validation and Sanitization:**

```c
// Input validation system
typedef struct {
    u16 lastValidButton;
    s8 lastValidStickX;
    s8 lastValidStickY;
    u8 errorCount;
} InputValidator;

// Validate input data
u8 InputValidator_Validate(InputValidator* validator, Input* input) {
    u8 isValid = 1;
    
    // Check for invalid button combinations
    u16 button = input->cur.button;
    if ((button & BTN_DLEFT) && (button & BTN_DRIGHT)) {
        // Left and right dpad pressed simultaneously (impossible)
        isValid = 0;
    }
    
    if ((button & BTN_DUP) && (button & BTN_DDOWN)) {
        // Up and down dpad pressed simultaneously (impossible)
        isValid = 0;
    }
    
    // Check for invalid stick values
    if (input->cur.stick_x < -80 || input->cur.stick_x > 80) {
        isValid = 0;
    }
    
    if (input->cur.stick_y < -80 || input->cur.stick_y > 80) {
        isValid = 0;
    }
    
    // Check for sudden impossible changes
    s8 stickDeltaX = input->cur.stick_x - validator->lastValidStickX;
    s8 stickDeltaY = input->cur.stick_y - validator->lastValidStickY;
    
    if (abs(stickDeltaX) > 60 || abs(stickDeltaY) > 60) {
        // Stick moved too far in one frame
        isValid = 0;
    }
    
    if (isValid) {
        // Store valid input
        validator->lastValidButton = button;
        validator->lastValidStickX = input->cur.stick_x;
        validator->lastValidStickY = input->cur.stick_y;
        validator->errorCount = 0;
    } else {
        // Use last valid input
        input->cur.button = validator->lastValidButton;
        input->cur.stick_x = validator->lastValidStickX;
        input->cur.stick_y = validator->lastValidStickY;
        validator->errorCount++;
        
        if (validator->errorCount > 10) {
            // Too many errors, might be hardware issue
            PRINTF("Warning: Controller input validation errors\n");
        }
    }
    
    return isValid;
}
```

## Conclusion

The Input System in OOT provides a robust and flexible framework for handling controller input across all game systems. Understanding its architecture is crucial for:

- Implementing custom input handlers and controls
- Creating smooth and responsive gameplay mechanics
- Debugging input-related issues
- Optimizing input processing performance
- Understanding the integration between input and game systems

The system's multi-layered design allows for efficient processing of controller data while providing high-level abstractions for game logic. The sophisticated filtering and processing systems ensure that input feels responsive and natural to players while maintaining the precision needed for a complex action-adventure game.

**Key Files Reference:**
- `src/code/padmgr.c` - Core controller management and polling
- `src/libu64/pad.c` - Input utility functions
- `src/overlays/actors/ovl_player_actor/z_player.c` - Player input integration
- `src/audio/game/general.c` - Ocarina input processing
- `src/code/z_frame_advance.c` - Frame advance input system
- `src/code/game.c` - Debug input processing
- `include/controller.h` - Input system definitions

## Additional Resources

For more detailed information about specific aspects of the input system, refer to:
- Individual actor implementations for custom input handling
- Player system documentation for movement and action input
- Audio system documentation for ocarina input processing
- UI system documentation for menu and interface input
- Debug system documentation for development input features 