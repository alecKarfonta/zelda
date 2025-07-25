#ifndef DO_ACTION_STATIC_H
#define DO_ACTION_STATIC_H

#include "ultra64.h"
#include "tex_len.h"
#include "versions.h"

#define DO_ACTION_TEX_WIDTH 48
#define DO_ACTION_TEX_HEIGHT 16
#define DO_ACTION_TEX_SIZE (DO_ACTION_TEX_WIDTH * DO_ACTION_TEX_HEIGHT / 2)

#if OOT_NTSC

extern u64 gAttackDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gCheckDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gEnterDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gReturnDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gOpenDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gJumpDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gDecideDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gDiveDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gFasterDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gThrowDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gUnusedNaviDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gClimbDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gDropDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gDownDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gSaveDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gSpeakDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNextDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gGrabDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gStopDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gPutAwayDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gReelDoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum1DoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum2DoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum3DoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum4DoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum5DoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum6DoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum7DoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum8DoActionJPNTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];

#endif

extern u64 gAttackDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gCheckDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gEnterDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gReturnDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gOpenDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gJumpDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gDecideDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gDiveDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gFasterDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gThrowDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gUnusedNaviDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gClimbDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gDropDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gDownDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gSaveDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gSpeakDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNextDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gGrabDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gStopDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gPutAwayDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gReelDoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum1DoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum2DoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum3DoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum4DoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum5DoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum6DoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum7DoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum8DoActionENGTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];

#if OOT_PAL

extern u64 gAttackDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gCheckDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gEnterDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gReturnDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gOpenDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gJumpDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gDecideDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gDiveDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gFasterDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gThrowDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gUnusedNaviDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gClimbDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gDropDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gDownDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gSaveDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gSpeakDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNextDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gGrabDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gStopDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gPutAwayDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gReelDoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum1DoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum2DoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum3DoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum4DoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum5DoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum6DoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum7DoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum8DoActionGERTex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];

extern u64 gAttackDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gCheckDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gEnterDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gReturnDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gOpenDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gJumpDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gDecideDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gDiveDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gFasterDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gThrowDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gUnusedNaviDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gClimbDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gDropDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gDownDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gSaveDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gSpeakDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNextDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gGrabDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gStopDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gPutAwayDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gReelDoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum1DoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum2DoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum3DoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum4DoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum5DoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum6DoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum7DoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];
extern u64 gNum8DoActionFRATex[TEX_LEN(u64, DO_ACTION_TEX_WIDTH, DO_ACTION_TEX_HEIGHT, 4)];

#endif

#endif
