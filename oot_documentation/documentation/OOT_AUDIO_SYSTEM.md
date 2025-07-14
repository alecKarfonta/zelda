# OOT Audio System Deep Dive

## Overview

This document provides a comprehensive analysis of the Audio System in The Legend of Zelda: Ocarina of Time (OOT) based on examination of the actual decomp source code. The audio system is a sophisticated multi-threaded architecture that handles background music, sound effects, interactive music (including the ocarina), and environmental audio through a combination of sequence-based music and real-time sound generation.

## Architecture Overview

### Audio Thread Structure

The audio system operates on a separate thread from the main game thread, with communication handled through message queues and command buffers:

**Audio Thread Management (`audio_thread_manager.c:93`):**
```c
void AudioMgr_ThreadEntry(void* arg) {
    AudioMgr* audioMgr = (AudioMgr*)arg;
    IrqMgrClient irqClient;
    s16* msg = NULL;
    
    PRINTF(T("オーディオマネージャスレッド実行開始\n", "Start running audio manager thread\n"));
    
    // Initialize audio driver
    Audio_Init();
    AudioLoad_SetDmaHandler(DmaMgr_AudioDmaHandler);
    Audio_InitSound();
    
    // Fill init queue to signal that the audio driver is initialized
    osSendMesg(&audioMgr->initQueue, NULL, OS_MESG_BLOCK);
    
    IrqMgr_AddClient(audioMgr->irqMgr, &irqClient, &audioMgr->interruptQueue);
    
    // Spin waiting for events
    for (;;) {
        osRecvMesg(&audioMgr->interruptQueue, (OSMesg*)&msg, OS_MESG_BLOCK);
        
        switch (*msg) {
            case OS_SC_RETRACE_MSG:
                AudioMgr_HandleRetrace(audioMgr);
                break;
            case OS_SC_PRE_NMI_MSG:
                AudioMgr_HandlePreNMI(audioMgr);
                break;
        }
    }
}
```

### Core Audio Context

**Audio Context Structure (`audio_internal/load.c:1335`):**
```c
void AudioLoad_Init(void* heap, u32 heapSize) {
    gAudioCtx.soundOutputMode = SOUND_OUTPUT_STEREO;
    gAudioCtx.curTask = NULL;
    gAudioCtx.rspTask[0].task.t.data_size = 0;
    gAudioCtx.rspTask[1].task.t.data_size = 0;
    
    osCreateMesgQueue(&gAudioCtx.syncDmaQueue, &gAudioCtx.syncDmaMesg, 1);
    osCreateMesgQueue(&gAudioCtx.curAudioFrameDmaQueue, gAudioCtx.curAudioFrameDmaMsgBuf,
                      ARRAY_COUNT(gAudioCtx.curAudioFrameDmaMsgBuf));
    osCreateMesgQueue(&gAudioCtx.externalLoadQueue, gAudioCtx.externalLoadMsgBuf,
                      ARRAY_COUNT(gAudioCtx.externalLoadMsgBuf));
    
    // Initialize heap and memory pools
    if (heap == NULL) {
        gAudioCtx.audioHeap = gAudioHeap;
        gAudioCtx.audioHeapSize = gAudioHeapInitSizes.heapSize;
    } else {
        gAudioCtx.audioHeap = heap;
        gAudioCtx.audioHeapSize = heapSize;
    }
    
    // Initialize audio tables
    gAudioCtx.sequenceTable = &gSequenceTable;
    gAudioCtx.soundFontTable = &gSoundFontTable;
    gAudioCtx.sampleBankTable = &gSampleBankTable;
    gAudioCtx.sequenceFontTable = gSequenceFontTable;
}
```

## Audio Update System

### Main Audio Update Loop

**Audio Update Function (`audio/game/general.c:2324`):**
```c
void Audio_Update(void) {
    if (func_800FAD34() == 0) {
        sAudioUpdateTaskStart = gAudioCtx.totalTaskCount;
        sAudioUpdateStartTime = osGetTime();
        
        // Update ocarina system
        AudioOcarina_Update();
        
        // Update environmental audio
        Audio_StepFreqLerp(&sRiverFreqScaleLerp);
        Audio_StepFreqLerp(&sWaterfallFreqScaleLerp);
        Audio_UpdateRiverSoundVolumes();
        
        // Update sequence system
        Audio_UpdateSceneSequenceResumePoint();
        Audio_UpdateFanfare();
        
        // Clear Saria's song if using specific audio spec
        if (gAudioSpecId == 7) {
            Audio_ClearSariaBgm();
        }
        
        // Process sound effects and sequences
        Audio_ProcessSfxRequests();
        Audio_ProcessSeqCmds();
        func_800F8F88();
        Audio_UpdateActiveSequences();
        
        // Schedule audio thread commands
        AudioThread_ScheduleProcessCmds();
        
        sAudioUpdateTaskEnd = gAudioCtx.totalTaskCount;
        sAudioUpdateEndTime = osGetTime();
    }
}
```

### Audio Thread Update Implementation

**Audio Thread Update (`audio/internal/thread.c:40`):**
```c
AudioTask* AudioThread_UpdateImpl(void) {
    u32 samplesRemainingInAi;
    s32 abiCmdCnt;
    s16* curAiBuffer;
    OSTask_t* task;
    s32 index;
    
    gAudioCtx.totalTaskCount++;
    
    // Handle audio frame processing
    if (gAudioCtx.totalTaskCount % (gAudioCtx.audioBufferParameters.specUnk4) != 0) {
        if (gAudioCustomUpdateFunction != NULL) {
            gAudioCustomUpdateFunction();
        }
        return NULL;
    }
    
    // Send task start message
    osSendMesg(gAudioCtx.taskStartQueueP, (OSMesg)gAudioCtx.totalTaskCount, OS_MESG_NOBLOCK);
    
    // Switch audio buffer index
    gAudioCtx.rspTaskIndex ^= 1;
    gAudioCtx.curAiBufIndex++;
    gAudioCtx.curAiBufIndex %= 3;
    
    // Set up AI buffer
    index = (gAudioCtx.curAiBufIndex - 2 + 3) % 3;
    samplesRemainingInAi = osAiGetLength() / 4;
    
    if (gAudioCtx.resetTimer < 16) {
        if (gAudioCtx.aiBufLengths[index] != 0) {
            osAiSetNextBuffer(gAudioCtx.aiBuffers[index], gAudioCtx.aiBufLengths[index] * 4);
        }
    }
    
    // Process audio commands
    gAudioCtx.curAbiCmdBuf = 
        AudioSynth_Update(gAudioCtx.curAbiCmdBuf, &abiCmdCnt, curAiBuffer, gAudioCtx.aiBufLengths[index]);
    
    // Update audio random seed
    gAudioCtx.audioRandom = (gAudioCtx.audioRandom + gAudioCtx.totalTaskCount) * osGetCount();
    
    // Set up RSP audio task
    index = gAudioCtx.rspTaskIndex;
    task = &gAudioCtx.curTask->task.t;
    task->type = M_AUDTASK;
    task->flags = 0;
    task->ucode_boot = aspMainTextStart;
    task->ucode_boot_size = SP_UCODE_SIZE;
    task->ucode = aspMainTextStart;
    task->ucode_size = SP_UCODE_SIZE;
    task->data_ptr = (u64*)gAudioCtx.abiCmdBufs[index];
    task->data_size = abiCmdCnt * sizeof(Acmd);
    
    return gAudioCtx.curTask;
}
```

## Sequence Management System

### Sequence Player Architecture

**Sequence Initialization (`audio/game/sequence.c:45`):**
```c
void Audio_StartSequence(u8 seqPlayerIndex, u8 seqId, u8 seqArgs, u16 fadeInDuration) {
    u8 channelIndex;
    u16 skipTicks;
    
    if (!gStartSeqDisabled || (seqPlayerIndex == SEQ_PLAYER_SFX)) {
        seqArgs &= 0x7F;
        
        // Handle debug mode with time skipping
        if (seqArgs == 0x7F) {
            skipTicks = (fadeInDuration >> 3) * 60 * gAudioCtx.audioBufferParameters.ticksPerUpdate;
            AUDIOCMD_GLOBAL_INIT_SEQPLAYER_SKIP_TICKS((u32)seqPlayerIndex, (u32)seqId, skipTicks);
        } else {
            // Normal sequence initialization
            AUDIOCMD_GLOBAL_INIT_SEQPLAYER((u32)seqPlayerIndex, (u32)seqId,
                                         (fadeInDuration * (u16)gAudioCtx.audioBufferParameters.ticksPerUpdate) / 4);
        }
        
        // Set up active sequence tracking
        gActiveSeqs[seqPlayerIndex].seqId = seqId | (seqArgs << 8);
        gActiveSeqs[seqPlayerIndex].prevSeqId = seqId | (seqArgs << 8);
        
        // Apply current volume if not at default
        if (gActiveSeqs[seqPlayerIndex].volCur != 1.0f) {
            AUDIOCMD_SEQPLAYER_FADE_VOLUME_SCALE((u32)seqPlayerIndex, gActiveSeqs[seqPlayerIndex].volCur);
        }
        
        // Reset sequence state
        gActiveSeqs[seqPlayerIndex].tempoTimer = 0;
        gActiveSeqs[seqPlayerIndex].tempoOriginal = 0;
        gActiveSeqs[seqPlayerIndex].tempoCmd = 0;
        
        // Initialize channel data
        for (channelIndex = 0; channelIndex < SEQ_NUM_CHANNELS; channelIndex++) {
            gActiveSeqs[seqPlayerIndex].channelData[channelIndex].volCur = 1.0f;
            gActiveSeqs[seqPlayerIndex].channelData[channelIndex].volTimer = 0;
            gActiveSeqs[seqPlayerIndex].channelData[channelIndex].freqScaleCur = 1.0f;
            gActiveSeqs[seqPlayerIndex].channelData[channelIndex].freqScaleTimer = 0;
        }
        
        gActiveSeqs[seqPlayerIndex].freqScaleChannelFlags = 0;
        gActiveSeqs[seqPlayerIndex].volChannelFlags = 0;
    }
}
```

### Sequence Command Processing

**Sequence Command Handler (`audio/game/sequence.c:200`):**
```c
void Audio_ProcessSeqCmd(u32 cmd) {
    u8 op = cmd >> 28;
    u8 seqPlayerIndex = (cmd >> 24) & 0xF;
    u8 subOp;
    u8 port;
    u8 channelIndex;
    u8 val;
    u16 val2;
    
    switch (op) {
        case SEQCMD_OP_PLAY_SEQUENCE:
            port = (cmd >> 16) & 0xFF;
            val = cmd & 0xFF;
            Audio_StartSequence(seqPlayerIndex, val, 0, (u16)port);
            break;
            
        case SEQCMD_OP_STOP_SEQUENCE:
            port = (cmd >> 16) & 0xFF;
            val = cmd & 0xFF;
            if (val == 0) {
                Audio_StopSequence(seqPlayerIndex, (u16)port);
            } else {
                Audio_StopSequence(seqPlayerIndex, val);
            }
            break;
            
        case SEQCMD_OP_QUEUE_SEQUENCE:
            port = (cmd >> 16) & 0xFF;
            val = cmd & 0xFF;
            Audio_QueueSequence(seqPlayerIndex, val, (u16)port, 10);
            break;
            
        case SEQCMD_OP_UNQUEUE_SEQUENCE:
            val = cmd & 0xFF;
            Audio_UnqueueSequence(seqPlayerIndex, val);
            break;
            
        case SEQCMD_OP_SET_SEQPLAYER_VOLUME:
            port = (cmd >> 16) & 0xFF;
            val = cmd & 0xFF;
            Audio_SetSequencePlayerVolume(seqPlayerIndex, port, val);
            break;
            
        case SEQCMD_OP_SET_SEQPLAYER_FREQ:
            val2 = cmd & 0xFFFF;
            Audio_SetSequencePlayerFreq(seqPlayerIndex, *(f32*)&val2);
            break;
            
        case SEQCMD_OP_SET_CHANNEL_VOLUME:
            channelIndex = (cmd >> 16) & 0xFF;
            port = (cmd >> 8) & 0xFF;
            val = cmd & 0xFF;
            Audio_SetChannelVolume(seqPlayerIndex, channelIndex, port, val);
            break;
            
        case SEQCMD_OP_GLOBAL_CMD:
            subOp = (cmd & 0xF00) >> 8;
            val = cmd & 0xFF;
            switch (subOp) {
                case SEQCMD_SUB_OP_GLOBAL_SET_SOUND_OUTPUT_MODE:
                    AUDIOCMD_GLOBAL_SET_SOUND_OUTPUT_MODE(gSoundOutputModes[val]);
                    break;
                case SEQCMD_SUB_OP_GLOBAL_DISABLE_NEW_SEQUENCES:
                    gStartSeqDisabled = val & 1;
                    break;
            }
            break;
            
        case SEQCMD_OP_RESET_AUDIO_HEAP:
            // Reset audio heap based on specifications
            specId = cmd & 0xFF;
            gSfxChannelLayout = (cmd & 0xFF00) >> 8;
            oldSpecId = gAudioSpecId;
            gAudioSpecId = specId;
            AudioThread_ResetAudioHeap(specId);
            func_800F71BC(oldSpecId);
            AUDIOCMD_GLOBAL_STOP_AUDIOCMDS();
            break;
    }
}
```

## Sound Effects System

### SFX Channel Architecture

**SFX Channel Configuration (`audio/game/general.c:36`):**
```c
typedef enum SfxChannelIndex {
    /* 0x0 */ SFX_CHANNEL_PLAYER0,    // SfxPlayerBank
    /* 0x1 */ SFX_CHANNEL_PLAYER1,
    /* 0x2 */ SFX_CHANNEL_PLAYER2,
    /* 0x3 */ SFX_CHANNEL_ITEM0,      // SfxItemBank
    /* 0x4 */ SFX_CHANNEL_ITEM1,
    /* 0x5 */ SFX_CHANNEL_ENV0,       // SfxEnvironmentBank
    /* 0x6 */ SFX_CHANNEL_ENV1,
    /* 0x7 */ SFX_CHANNEL_ENV2,
    /* 0x8 */ SFX_CHANNEL_ENEMY0,     // SfxEnemyBank
    /* 0x9 */ SFX_CHANNEL_ENEMY1,
    /* 0xA */ SFX_CHANNEL_ENEMY2,
    /* 0xB */ SFX_CHANNEL_SYSTEM0,    // SfxSystemBank
    /* 0xC */ SFX_CHANNEL_SYSTEM1,
    /* 0xD */ SFX_CHANNEL_OCARINA,    // SfxOcarinaBank
    /* 0xE */ SFX_CHANNEL_VOICE0,     // SfxVoiceBank
    /* 0xF */ SFX_CHANNEL_VOICE1
} SfxChannelIndex;
```

### SFX Playback System

**SFX Request Processing (`audio/game/sfx.c:72`):**
```c
void Audio_PlaySfxGeneral(u16 sfxId, Vec3f* pos, u8 token, f32* freqScale, f32* vol, s8* reverbAdd) {
    u8 i;
    SfxRequest* req;
    
    if (!gSfxBankMuted[SFX_BANK_SHIFT(sfxId)]) {
        req = &sSfxRequests[gSfxRequestWriteIndex];
        
        // Handle SFX swapping for debug purposes
        for (i = 0; i < 10; i++) {
            if (sfxId == gAudioSfxSwapSource[i]) {
                if (gAudioSfxSwapMode[i] == 0) { // "SWAP"
                    sfxId = gAudioSfxSwapTarget[i];
                } else { // "ADD"
                    req->sfxId = gAudioSfxSwapTarget[i];
                    req->pos = pos;
                    req->token = token;
                    req->freqScale = freqScale;
                    req->vol = vol;
                    req->reverbAdd = reverbAdd;
                    gSfxRequestWriteIndex++;
                    req = &sSfxRequests[gSfxRequestWriteIndex];
                }
                break;
            }
        }
        
        // Set up SFX request
        req->sfxId = sfxId;
        req->pos = pos;
        req->token = token;
        req->freqScale = freqScale;
        req->vol = vol;
        req->reverbAdd = reverbAdd;
        gSfxRequestWriteIndex++;
    }
}
```

### SFX Volume and Positioning

**SFX Volume Calculation (`audio/game/general.c:2372`):**
```c
f32 Audio_ComputeSfxVolume(u8 bankId, u8 entryIdx) {
    SfxBankEntry* bankEntry = &gSfxBanks[bankId][entryIdx];
    f32 minDist;
    f32 baseDist;
    f32 ret;
    
    // Override volume calculation for certain flags
    if (bankEntry->sfxParams & SFX_FLAG_13) {
        return 1.0f;
    }
    
    if (bankEntry->dist > 10000.0f) {
        ret = 0.0f;
    } else {
        // Calculate base distance based on SFX parameters
        switch ((bankEntry->sfxParams & SFX_PARAM_01_MASK) >> SFX_PARAM_01_SHIFT) {
            case 1:
                baseDist = 10000.0f / 15.0f;
                break;
            case 2:
                baseDist = 10000.0f / 10.5f;
                break;
            case 3:
                baseDist = 10000.0f / 2.6f;
                break;
            default:
                baseDist = 10000.0f / 20.0f;
                break;
        }
        
        // Calculate minimum distance
        minDist = baseDist * 0.16f;
        
        if (bankEntry->dist < minDist) {
            ret = 1.0f;
        } else if (bankEntry->dist < baseDist) {
            ret = 1.0f - ((bankEntry->dist - minDist) / (baseDist - minDist)) * 0.4f;
        } else {
            ret = 0.6f * (1.0f - ((bankEntry->dist - baseDist) / (10000.0f - baseDist)));
        }
    }
    
    return ret;
}
```

## Ocarina System

### Ocarina Input Processing

**Ocarina Controller Input (`audio/game/general.c:1278`):**
```c
void AudioOcarina_ReadControllerInput(void) {
    Input* input = &gAudioCtx.padMgr->inputs[0];
    
    sOcarinaInputButtonPrev = sOcarinaInputButtonCur;
    sOcarinaInputButtonCur = 0;
    
    // Map controller buttons to ocarina notes
    if (input->cur.button & BTN_A) {
        sOcarinaInputButtonCur |= OCARINA_BTN_A;
    }
    if (input->cur.button & BTN_CDOWN) {
        sOcarinaInputButtonCur |= OCARINA_BTN_CDOWN;
    }
    if (input->cur.button & BTN_CRIGHT) {
        sOcarinaInputButtonCur |= OCARINA_BTN_CRIGHT;
    }
    if (input->cur.button & BTN_CLEFT) {
        sOcarinaInputButtonCur |= OCARINA_BTN_CLEFT;
    }
    if (input->cur.button & BTN_CUP) {
        sOcarinaInputButtonCur |= OCARINA_BTN_CUP;
    }
    
    // Handle analog stick input for pitch bending
    if (gAudioCtx.padMgr->inputs[0].cur.stick_x > 20) {
        sOcarinaInputStickX = gAudioCtx.padMgr->inputs[0].cur.stick_x;
    } else if (gAudioCtx.padMgr->inputs[0].cur.stick_x < -20) {
        sOcarinaInputStickX = gAudioCtx.padMgr->inputs[0].cur.stick_x;
    } else {
        sOcarinaInputStickX = 0;
    }
    
    // Calculate button press/release events
    sOcarinaInputButtonPress = sOcarinaInputButtonCur & (sOcarinaInputButtonCur ^ sOcarinaInputButtonPrev);
}
```

### Ocarina Song Recognition

**Song Recognition System (`audio/game/general.c:1462`):**
```c
void AudioOcarina_CheckSongsWithMusicStaff(void) {
    u8 i;
    u8 pitchAndBFlatFlag;
    u8 nextNote;
    u8 sPrevOcarinaPitch;
    
    if (sCurOcarinaPitch != OCARINA_PITCH_NONE) {
        // Check if note matches expected song pattern
        for (i = 0; i < ARRAY_COUNT(gOcarinaSongInfo); i++) {
            if (gOcarinaSongInfo[i].enabled && (gOcarinaSongInfo[i].playbackState == 0)) {
                pitchAndBFlatFlag = gOcarinaSongInfo[i].notes[gOcarinaSongInfo[i].noteIdx];
                
                // Check if current note matches expected note
                if ((pitchAndBFlatFlag & 0x3F) == sCurOcarinaPitch) {
                    gOcarinaSongInfo[i].noteIdx++;
                    
                    // Check if song is complete
                    if (gOcarinaSongInfo[i].noteIdx >= gOcarinaSongInfo[i].len) {
                        // Song completed successfully
                        gOcarinaSongInfo[i].playbackState = 1;
                        if (gOcarinaSongInfo[i].playbackState == 1) {
                            AudioOcarina_SetPlaybackSong(i + 1, 1);
                        }
                    }
                } else {
                    // Note mismatch, reset song progress
                    gOcarinaSongInfo[i].noteIdx = 0;
                    
                    // Check if current note is first note of this song
                    if ((gOcarinaSongInfo[i].notes[0] & 0x3F) == sCurOcarinaPitch) {
                        gOcarinaSongInfo[i].noteIdx = 1;
                    }
                }
            }
        }
    }
}
```

### Ocarina Instrument Management

**Ocarina Instrument Setup (`audio/game/general.c:1756`):**
```c
void AudioOcarina_SetInstrument(u8 ocarinaInstrumentId) {
    if (sOcarinaInstrumentId == ocarinaInstrumentId) {
        return;
    }
    
    // Set ocarina instrument channel
    SEQCMD_SET_CHANNEL_IO(SEQ_PLAYER_SFX, SFX_CHANNEL_OCARINA, 1, ocarinaInstrumentId);
    sOcarinaInstrumentId = ocarinaInstrumentId;
    
    if (ocarinaInstrumentId == OCARINA_INSTRUMENT_OFF) {
        // Disable ocarina
        sOcarinaInputButtonCur = 0;
        sOcarinaInputButtonPrev = 0;
        sOcarinaInputButtonPress = 0;
        sOcarinaInputButtonStart = 0xFFFF;
        
        AudioOcarina_PlayControllerInput(false);
        Audio_StopSfxById(NA_SE_OC_OCARINA);
        Audio_SetSfxBanksMute(0);
        sPlaybackState = 0;
        sPlaybackStaffPos = 0;
        sIsOcarinaInputEnabled = false;
        sOcarinaFlags = 0;
        
        // Return to full volume for background BGM
        Audio_ClearBGMMute(SFX_CHANNEL_OCARINA);
    } else {
        // Enable ocarina
        sOcarinaInputButtonCur = 0;
        AudioOcarina_ReadControllerInput();
        
        // Store button used to activate ocarina
        sOcarinaInputButtonStart = sOcarinaInputButtonCur;
        
        // Lower background BGM volume while playing ocarina
        Audio_QueueSeqCmdMute(SFX_CHANNEL_OCARINA);
    }
}
```

## Audio Synthesis System

### Audio Synthesis Update

**Audio Synthesis (`audio/internal/synthesis.c:151`):**
```c
Acmd* AudioSynth_Update(Acmd* cmdStart, s32* cmdCnt, s16* aiStart, s32 aiBufLen) {
    s32 chunkLen;
    s16* aiBufP;
    Acmd* cmdP;
    s32 i;
    s32 j;
    
    cmdP = cmdStart;
    
    // Process sequences for each tick
    for (i = gAudioCtx.audioBufferParameters.ticksPerUpdate; i > 0; i--) {
        AudioSeq_ProcessSequences(i - 1);
        func_800DB03C(gAudioCtx.audioBufferParameters.ticksPerUpdate - i);
    }
    
    aiBufP = aiStart;
    gAudioCtx.curLoadedBook = NULL;
    
    // Process audio chunks
    for (i = gAudioCtx.audioBufferParameters.ticksPerUpdate; i > 0; i--) {
        // Calculate chunk size
        if (i == 1) {
            chunkLen = aiBufLen;
        } else if ((aiBufLen / i) >= gAudioCtx.audioBufferParameters.samplesPerTickMax) {
            chunkLen = gAudioCtx.audioBufferParameters.samplesPerTickMax;
        } else if (gAudioCtx.audioBufferParameters.samplesPerTickMin >= (aiBufLen / i)) {
            chunkLen = gAudioCtx.audioBufferParameters.samplesPerTickMin;
        } else {
            chunkLen = gAudioCtx.audioBufferParameters.samplesPerTick;
        }
        
        // Initialize reverb for this chunk
        for (j = 0; j < gAudioCtx.numSynthesisReverbs; j++) {
            if (gAudioCtx.synthesisReverbs[j].useReverb) {
                AudioSynth_InitNextRingBuf(chunkLen, gAudioCtx.audioBufferParameters.ticksPerUpdate - i, j);
            }
        }
        
        // Process one audio update
        cmdP = AudioSynth_DoOneAudioUpdate(aiBufP, chunkLen, cmdP, 
                                          gAudioCtx.audioBufferParameters.ticksPerUpdate - i);
        
        aiBufLen -= chunkLen;
        aiBufP += 2 * chunkLen;
    }
    
    // Update reverb state
    for (j = 0; j < gAudioCtx.numSynthesisReverbs; j++) {
        if (gAudioCtx.synthesisReverbs[j].framesToIgnore != 0) {
            gAudioCtx.synthesisReverbs[j].framesToIgnore--;
        }
        gAudioCtx.synthesisReverbs[j].curFrame ^= 1;
    }
    
    *cmdCnt = cmdP - cmdStart;
    return cmdP;
}
```

### Audio Note Processing

**Note Processing (`audio/internal/synthesis.c:695`):**
```c
Acmd* AudioSynth_ProcessNote(s32 noteIndex, NoteSubEu* noteSubEu, NoteSynthesisState* synthState, 
                           s16* aiBuf, s32 aiBufLen, Acmd* cmd, s32 updateIndex) {
    Sample* sample;
    AdpcmLoop* loopInfo;
    s32 nSamplesUntilLoopEnd;
    s32 nSamplesInThisIteration;
    s32 noteFinished;
    s32 flags;
    u16 resamplingRateFixedPoint;
    Note* note;
    
    note = &gAudioCtx.notes[noteIndex];
    flags = A_CONTINUE;
    
    // Process sample data
    if (noteSubEu->bitField0.enabled) {
        sample = noteSubEu->sound.sample;
        
        if (sample != NULL) {
            // Load wave samples
            cmd = AudioSynth_LoadWaveSamples(cmd, noteSubEu, synthState, numSamplesToLoad);
            
            // Apply envelope processing
            cmd = AudioSynth_ProcessEnvelope(cmd, noteSubEu, synthState, aiBufLen, 
                                           dmemSrc, haasEffectDelaySide, flags);
            
            // Handle sample looping
            if (noteSubEu->bitField0.hasAdpcmLoop) {
                loopInfo = sample->loop;
                nSamplesUntilLoopEnd = loopInfo->end - synthState->samplePos;
                
                if (nSamplesUntilLoopEnd > 0) {
                    nSamplesInThisIteration = MIN(nSamplesUntilLoopEnd, nSamplesToProcess);
                } else {
                    // Handle loop restart
                    synthState->samplePos = loopInfo->start;
                    nSamplesInThisIteration = nSamplesToProcess;
                }
            }
        }
    }
    
    return cmd;
}
```

## Environmental Audio System

### Nature Ambience System

**Nature Ambience Playback (`audio/game/general.c:4032`):**
```c
void Audio_PlayNatureAmbienceSequence(u8 natureAmbienceId) {
    u8 i = 0;
    u8 channelIdx;
    u8 ioPort;
    u8 ioData;
    
    if ((gActiveSeqs[SEQ_PLAYER_BGM_MAIN].seqId == NA_BGM_DISABLED) ||
        !(sSeqFlags[gActiveSeqs[SEQ_PLAYER_BGM_MAIN].seqId & 0xFF] & SEQ_FLAG_NO_AMBIENCE)) {
        
        // Store previous ambience sequence ID
        if (gActiveSeqs[SEQ_PLAYER_BGM_MAIN].seqId != NA_BGM_NATURE_AMBIENCE) {
            sPrevAmbienceSeqId = gActiveSeqs[SEQ_PLAYER_BGM_MAIN].seqId;
        }
        
        // Start nature ambience sequence
        Audio_StartNatureAmbienceSequence(sNatureAmbienceDataIO[natureAmbienceId].playerIO,
                                         sNatureAmbienceDataIO[natureAmbienceId].channelMask);
        
        // Configure channel I/O parameters
        while ((sNatureAmbienceDataIO[natureAmbienceId].channelIO[i] != 0xFF) && (i < 100)) {
            channelIdx = sNatureAmbienceDataIO[natureAmbienceId].channelIO[i++];
            ioPort = sNatureAmbienceDataIO[natureAmbienceId].channelIO[i++];
            ioData = sNatureAmbienceDataIO[natureAmbienceId].channelIO[i++];
            SEQCMD_SET_CHANNEL_IO(SEQ_PLAYER_BGM_MAIN, channelIdx, ioPort, ioData);
        }
        
        // Set sound output mode
        SEQCMD_SET_CHANNEL_IO(SEQ_PLAYER_BGM_MAIN, NATURE_CHANNEL_UNK, CHANNEL_IO_PORT_7, sSoundOutputMode);
    }
}
```

### River and Waterfall Audio

**River Sound Volume Updates (`audio/game/general.c:3022`):**
```c
void Audio_UpdateRiverSoundVolumes(void) {
    f32 temp;
    f32 volumeScale;
    
    if (sRiverSoundBgmPlayerIO == 0) {
        return;
    }
    
    // Calculate volume based on distance and frequency scaling
    temp = sRiverFreqScaleLerp.value;
    if (temp > 0.85f) {
        temp = 0.85f;
    }
    
    volumeScale = (temp < 0.13f) ? 0.0f : (temp - 0.13f) / 0.72f;
    
    // Apply volume to river sound channels
    SEQCMD_SET_CHANNEL_IO(SEQ_PLAYER_BGM_MAIN, sRiverSoundBgmPlayerIO & 0xFF, 
                         CHANNEL_IO_PORT_4, (u8)(volumeScale * 127.0f));
    SEQCMD_SET_CHANNEL_IO(SEQ_PLAYER_BGM_MAIN, (sRiverSoundBgmPlayerIO >> 8) & 0xFF, 
                         CHANNEL_IO_PORT_4, (u8)(volumeScale * 127.0f));
    
    // Handle waterfall sounds
    if (sWaterfallSoundBgmPlayerIO != 0) {
        temp = sWaterfallFreqScaleLerp.value;
        if (temp > 0.85f) {
            temp = 0.85f;
        }
        
        volumeScale = (temp < 0.13f) ? 0.0f : (temp - 0.13f) / 0.72f;
        
        SEQCMD_SET_CHANNEL_IO(SEQ_PLAYER_BGM_MAIN, sWaterfallSoundBgmPlayerIO & 0xFF, 
                             CHANNEL_IO_PORT_4, (u8)(volumeScale * 127.0f));
        SEQCMD_SET_CHANNEL_IO(SEQ_PLAYER_BGM_MAIN, (sWaterfallSoundBgmPlayerIO >> 8) & 0xFF, 
                             CHANNEL_IO_PORT_4, (u8)(volumeScale * 127.0f));
    }
}
```

## Audio Command System

### Audio Thread Commands

**Audio Thread Command Processing (`audio/internal/thread.c:468`):**
```c
void AudioThread_ProcessCmd(AudioCmd* cmd) {
    SequencePlayer* seqPlayer;
    u16 threadCmdChannelMask;
    s32 channelIndex;
    
    // Handle global commands
    if ((cmd->op & 0xF0) == 0xF0) {
        AudioThread_ProcessGlobalCmd(cmd);
        return;
    }
    
    // Validate sequence player index
    if (cmd->arg0 < gAudioCtx.audioBufferParameters.numSequencePlayers) {
        seqPlayer = &gAudioCtx.seqPlayers[cmd->arg0];
        
        // Handle global sequence commands
        if (cmd->op & 0x80) {
            AudioThread_ProcessGlobalCmd(cmd);
            return;
        }
        
        // Handle sequence player commands
        if (cmd->op & 0x40) {
            AudioThread_ProcessSeqPlayerCmd(seqPlayer, cmd);
            return;
        }
        
        // Handle channel-specific commands
        if (cmd->arg1 < SEQ_NUM_CHANNELS) {
            AudioThread_ProcessChannelCmd(seqPlayer->channels[cmd->arg1], cmd);
            return;
        } else if (cmd->arg1 == AUDIOCMD_ALL_CHANNELS) {
            // Apply command to all channels
            threadCmdChannelMask = gAudioCtx.threadCmdChannelMask[cmd->arg0];
            for (channelIndex = 0; channelIndex < SEQ_NUM_CHANNELS; channelIndex++) {
                if (threadCmdChannelMask & 1) {
                    AudioThread_ProcessChannelCmd(seqPlayer->channels[channelIndex], cmd);
                }
                threadCmdChannelMask = threadCmdChannelMask >> 1;
            }
        }
    }
}
```

### Global Audio Commands

**Global Command Processing (`audio/internal/thread.c:213`):**
```c
void AudioThread_ProcessGlobalCmd(AudioCmd* cmd) {
    s32 i;
    
    switch (cmd->op) {
        case AUDIOCMD_OP_GLOBAL_SYNC_LOAD_SEQ_PARTS:
            AudioLoad_SyncLoadSeqParts(cmd->arg1, cmd->arg2);
            break;
            
        case AUDIOCMD_OP_GLOBAL_INIT_SEQPLAYER:
            AudioLoad_SyncInitSeqPlayer(cmd->arg0, cmd->arg1, cmd->arg2);
            AudioThread_SetFadeInTimer(cmd->arg0, cmd->asInt);
            break;
            
        case AUDIOCMD_OP_GLOBAL_DISABLE_SEQPLAYER:
            if (gAudioCtx.seqPlayers[cmd->arg0].enabled) {
                if (cmd->asInt == 0) {
                    AudioSeq_SequencePlayerDisableAsFinished(&gAudioCtx.seqPlayers[cmd->arg0]);
                } else {
                    AudioThread_SetFadeOutTimer(cmd->arg0, cmd->asInt);
                }
            }
            break;
            
        case AUDIOCMD_OP_GLOBAL_SET_SOUND_OUTPUT_MODE:
            gAudioCtx.soundOutputMode = cmd->asUInt;
            break;
            
        case AUDIOCMD_OP_GLOBAL_MUTE:
            // Mute all sequence players
            for (i = 0; i < gAudioCtx.audioBufferParameters.numSequencePlayers; i++) {
                SequencePlayer* seqPlayer = &gAudioCtx.seqPlayers[i];
                seqPlayer->muted = true;
                seqPlayer->recalculateVolume = true;
            }
            break;
            
        case AUDIOCMD_OP_GLOBAL_UNMUTE:
            // Unmute all sequence players
            for (i = 0; i < gAudioCtx.audioBufferParameters.numSequencePlayers; i++) {
                SequencePlayer* seqPlayer = &gAudioCtx.seqPlayers[i];
                seqPlayer->muted = false;
                seqPlayer->recalculateVolume = true;
            }
            break;
    }
}
```

## Audio Memory Management

### Audio Heap System

**Audio Heap Management (`audio/internal/load.c:1384`):**
```c
void AudioHeap_InitMainPools(s32 initPoolSize) {
    void* addr;
    s32 remainingSize;
    s32 size;
    s32 i;
    
    // Initialize audio heap
    gAudioCtx.audioHeapSize = gAudioHeapInitSizes.heapSize;
    
    // Clear entire heap
    for (i = 0; i < (s32)gAudioCtx.audioHeapSize / 8; i++) {
        ((u64*)gAudioCtx.audioHeap)[i] = 0;
    }
    
    // Set up main pools
    addr = gAudioCtx.audioHeap;
    remainingSize = gAudioCtx.audioHeapSize;
    
    // Initialize init pool
    size = initPoolSize;
    AudioHeap_InitPool(&gAudioCtx.initPool, addr, size);
    addr = (u8*)addr + size;
    remainingSize -= size;
    
    // Initialize session pool with remaining space
    AudioHeap_InitPool(&gAudioCtx.sessionPool, addr, remainingSize);
    
    // Reset heap allocation state
    gAudioCtx.resetStatus = 1;
    AudioHeap_ResetStep();
}
```

### Audio Sample Loading

**Sample Loading System (`audio/internal/load.c:1500`):**
```c
void AudioLoad_SyncLoadSeqParts(s32 seqId, s32 arg1) {
    SequenceData* seqData;
    SoundFontData* soundFontData;
    s32 soundFontId;
    s32 i;
    
    // Load sequence data
    seqData = AudioLoad_SyncLoadSeq(seqId);
    
    if (seqData == NULL) {
        return;
    }
    
    // Load associated sound fonts
    for (i = 0; i < 16; i++) {
        soundFontId = seqData->soundFontId[i];
        if (soundFontId != 0xFF) {
            soundFontData = AudioLoad_SyncLoadSoundFont(soundFontId);
            if (soundFontData != NULL) {
                // Load sample banks for this sound font
                AudioLoad_SyncLoadSampleBanks(soundFontData);
            }
        }
    }
    
    // Finalize sequence loading
    AudioLoad_SyncInitSeqPlayer(0, seqId, arg1);
}
```

## Audio Debug System

### Audio Debug Features

**Audio Debug Interface (`audio/game/general.c:2314`):**
```c
void AudioDebug_Draw(GfxPrint* printer) {
    static u8 sDebugPage = PAGE_NON;
    static u8 sDebugPagePrev = PAGE_NON;
    
    if (sDebugPage != PAGE_NON) {
        switch (sDebugPage) {
            case PAGE_SOUND_CONTROL:
                AudioDebug_DrawSoundControl(printer);
                break;
                
            case PAGE_HEAP_INFO:
                AudioDebug_DrawHeapInfo(printer);
                break;
                
            case PAGE_SUB_TRACK_INFO:
                AudioDebug_DrawSubTrackInfo(printer);
                break;
                
            case PAGE_INTERFACE_INFO:
                AudioDebug_DrawInterfaceInfo(printer);
                break;
                
            case PAGE_SFX_SWAP:
                AudioDebug_DrawSfxSwap(printer);
                break;
                
            case PAGE_BLOCK_CHANGE_BGM:
                AudioDebug_DrawBlockChangeBgm(printer);
                break;
                
            case PAGE_OCARINA_TEST:
                AudioDebug_DrawOcarinaTest(printer);
                break;
                
            case PAGE_SFX_PARAMETER_CHANGE:
                AudioDebug_DrawSfxParameterChange(printer);
                break;
                
            case PAGE_SCROLL_PRINT:
                AudioDebug_DrawScrollPrint(printer);
                break;
        }
    }
}
```

## Practical Implications for Modding

### Custom Audio Integration

**Adding Custom Sound Effects:**
1. **SFX Bank Integration**: Add entries to appropriate SFX banks
2. **Sample Integration**: Include sample data in audio heap
3. **Playback Implementation**: Use existing SFX playback functions
4. **Positioning**: Implement 3D positional audio calculations

**Example Custom SFX Implementation:**
```c
// Custom SFX playback function
void CustomAudio_PlaySfx(u16 sfxId, Vec3f* pos, f32 volume) {
    f32 volScale = volume;
    
    // Play SFX with custom volume scaling
    Audio_PlaySfxGeneral(sfxId, pos, 0, &gSfxDefaultFreqAndVolScale, 
                        &volScale, &gSfxDefaultReverb);
}

// Custom ambient sound system
void CustomAudio_UpdateAmbientSounds(PlayState* play) {
    Player* player = GET_PLAYER(play);
    f32 distanceToWater = /* calculate distance */;
    f32 volumeScale = 1.0f - (distanceToWater / 1000.0f);
    
    if (volumeScale > 0.0f) {
        Vec3f waterPos = { /* water position */ };
        CustomAudio_PlaySfx(NA_SE_EV_WATER_WALL, &waterPos, volumeScale);
    }
}
```

### Custom Music Integration

**Adding Custom Sequences:**
1. **Sequence Data**: Create MIDI-based sequence data
2. **Sound Font Setup**: Configure instruments and samples
3. **Playback Integration**: Use sequence player system
4. **Dynamic Control**: Implement interactive music features

**Example Custom Music System:**
```c
// Custom dynamic music system
void CustomAudio_UpdateDynamicMusic(PlayState* play) {
    Player* player = GET_PLAYER(play);
    
    // Check player state for music changes
    if (player->stateFlags1 & PLAYER_STATE1_IN_WATER) {
        if (gActiveSeqs[SEQ_PLAYER_BGM_MAIN].seqId != CUSTOM_BGM_UNDERWATER) {
            Audio_StartSequence(SEQ_PLAYER_BGM_MAIN, CUSTOM_BGM_UNDERWATER, 0, 30);
        }
    } else {
        if (gActiveSeqs[SEQ_PLAYER_BGM_MAIN].seqId != CUSTOM_BGM_OVERWORLD) {
            Audio_StartSequence(SEQ_PLAYER_BGM_MAIN, CUSTOM_BGM_OVERWORLD, 0, 30);
        }
    }
}
```

### Performance Optimization

**Audio Performance Guidelines:**
1. **Memory Management**: Efficient use of audio heap
2. **Sample Optimization**: Compress samples appropriately
3. **Channel Usage**: Minimize simultaneous channel usage
4. **Update Frequency**: Optimize audio update frequency

**Memory Usage Optimization:**
```c
// Optimized audio memory usage
void CustomAudio_OptimizeMemoryUsage(void) {
    // Preload frequently used samples
    AudioLoad_SyncLoadSampleBank(CUSTOM_SAMPLE_BANK_COMMON);
    
    // Unload unused sequences
    for (int i = 0; i < MAX_SEQUENCES; i++) {
        if (!gActiveSeqs[i].enabled && gSeqData[i].loaded) {
            AudioLoad_UnloadSequence(i);
        }
    }
    
    // Optimize heap fragmentation
    AudioHeap_Defragment();
}
```

## Common Issues and Solutions

### Audio Debugging Techniques

**Debug Audio Issues:**
1. **Channel Monitoring**: Track active channels and their states
2. **Memory Tracking**: Monitor audio heap usage
3. **Sequence State**: Check sequence player states
4. **Command Queue**: Verify command processing

**Common Problems:**
- **Audio Dropouts**: Usually caused by memory exhaustion
- **Sequence Timing**: Incorrect tick calculations
- **SFX Conflicts**: Channel conflicts between different SFX
- **Memory Leaks**: Improper sequence/sample unloading

### Best Practices

**Audio System Guidelines:**
1. **Memory Management**: Careful heap allocation and deallocation
2. **Error Handling**: Proper validation of audio parameters
3. **Performance**: Efficient audio update loops
4. **Threading**: Proper synchronization between threads

**Code Organization:**
- **Modular Design**: Separate audio systems by function
- **State Management**: Clear audio state tracking
- **Resource Management**: Proper loading/unloading of audio data
- **Documentation**: Clear audio system documentation

## Conclusion

The OOT audio system represents a sophisticated approach to interactive audio on the N64 hardware. The multi-threaded architecture, combined with flexible sequence management and real-time synthesis capabilities, creates a rich audio experience that adapts to gameplay.

Key architectural strengths include:
- **Threaded Architecture**: Efficient separation of audio processing from main game loop
- **Flexible Sequence System**: Dynamic music control and interactive audio
- **3D Audio Processing**: Sophisticated positional audio calculations
- **Memory Efficiency**: Optimized audio heap management
- **Real-time Synthesis**: High-quality audio synthesis on limited hardware
- **Interactive Features**: Advanced ocarina system and dynamic music

Understanding this system is crucial for effective audio modding in OOT, as it provides the foundation for all sound and music in the game. The careful balance between audio quality, memory usage, and real-time performance demonstrates expert engineering that continues to influence modern game audio systems. 