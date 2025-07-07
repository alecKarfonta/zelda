// Snippet 3
// Success: False
// Compilation time: 0.090s

// Barrier Gauntlet actor that creates protective barriers
typedef struct {
    /* 0x0000 */ Actor actor;
    /* 0x014C */ ColliderCylinder collider;
    /* 0x0198 */ s16 timer;
    /* 0x019A */ s16 activeTime;
    /* 0x019C */ f32 barrierScale;
    /* 0x01A0 */ f32 targetScale;
} EnBarrier; // size = 0x01A4

static ColliderCylinderInit sCylinderInit = {
    {
        COLTYPE_NONE,
        AT_NONE,
        AC_ON | AC_TYPE_PLAYER,
        OC1_ON | OC1_TYPE_ALL,
        OC2_TYPE_2,
        COLSHAPE_CYLINDER,
    },
    {
        ELEMTYPE_UNK0,
        { 0x00000000, 0x00, 0x00 },
        { 0xFFCFFFFF, 0x00, 0x00 },
        TOUCH_NONE,
        BUMP_ON,
        OCELEM_ON,
    },
    { 40, 60, 0, { 0, 0, 0 } },
};

void EnBarrier_Init(Actor* thisx, PlayState* play) {
    EnBarrier* this = (EnBarrier*)thisx;
    
    Actor_SetScale(&this->actor, 0.0f);
    this->barrierScale = 0.0f;
    this->targetScale = 0.01f;
    this->timer = 0;
    this->activeTime = 100;
    
    Collider_InitCylinder(play, &this->collider);
    Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);
    
    this->actor.flags |= ACTOR_FLAG_4;
    this->actor.flags |= ACTOR_FLAG_0;
}

void EnBarrier_Destroy(Actor* thisx, PlayState* play) {
    EnBarrier* this = (EnBarrier*)thisx;
    Collider_DestroyCylinder(play, &this->collider);
}

void EnBarrier_Update(Actor* thisx, PlayState* play) {
    EnBarrier* this = (EnBarrier*)thisx;
    Player* player = GET_PLAYER(play);

    if (this->timer >= this->activeTime) {
        Actor_Kill(&this->actor);
        return;
    }

    this->timer++;
    
    // Smooth scale animation
    Math_SmoothStepToF(&this->barrierScale, this->targetScale, 0.3f, 0.02f, 0.001f);
    Actor_SetScale(&this->actor, this->barrierScale);
    
    // Update collision
    Collider_UpdateCylinder(&this->actor, &this->collider);
    CollisionCheck_SetAC(play, &play->colChkCtx, &this->collider.base);
    CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
}

void EnBarrier_Draw(Actor* thisx, PlayState* play) {
    EnBarrier* this = (EnBarrier*)thisx;
    
    OPEN_DISPS(play->state.gfxCtx);
    
    Gfx_SetupDL_25Opa(play->state.gfxCtx);
    
    Matrix_Translate(this->actor.world.pos.x, this->actor.world.pos.y, this->actor.world.pos.z, MTXMODE_NEW);
    Matrix_Scale(this->barrierScale, this->barrierScale, this->barrierScale, MTXMODE_APPLY);
    
    gSPMatrix(POLY_OPA_DISP++, Matrix_NewMtx(play->state.gfxCtx, __FILE__, __LINE__),
              G_MTX_NOPUSH | G_MTX_LOAD | G_MTX_MODELVIEW);
              
    gSPDisplayList(POLY_OPA_DISP++, gEffFlash1DL);
    
    CLOSE_DISPS(play->state.gfxCtx);
}

const ActorProfile En_Barrier_InitVars = {
    /**/ ACTOR_EN_BARRIER,
    /**/ ACTORCAT_PROP,
    /**/ FLAGS,
    /**/ OBJECT_GAMEPLAY_KEEP,
    /**/ sizeof(EnBarrier),
    /**/ EnBarrier_Init,
    /**/ EnBarrier_Destroy,
    /**/ EnBarrier_Update,
    /**/ EnBarrier_Draw
};