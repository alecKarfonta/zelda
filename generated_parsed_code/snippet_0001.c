// Snippet 1
// Success: False
// Compilation time: 0.098s

typedef struct {
    /* 0x0000 */ Actor actor;
    /* 0x014C */ s16 timer;
    /* 0x014E */ s16 flowState;
    /* 0x0150 */ f32 flowSpeed;
    /* 0x0154 */ f32 flowHeight;
    /* 0x0158 */ Vec3f originalPos;
    /* 0x0164 */ ColliderCylinder collider;
} EnFireFlow; // size = 0x1B0

static ColliderCylinderInit sCylinderInit = {
    {
        COLTYPE_NONE,
        AT_ON | AT_TYPE_ENEMY,
        AC_NONE,
        OC1_ON | OC1_TYPE_ALL,
        OC2_TYPE_2,
        COLSHAPE_CYLINDER,
    },
    {
        ELEMTYPE_UNK0,
        { 0x20000000, 0x01, 0x04 },
        { 0x00000000, 0x00, 0x00 },
        TOUCH_ON | TOUCH_SFX_NONE,
        BUMP_NONE,
        OCELEM_ON,
    },
    { 30, 50, 0, { 0, 0, 0 } },
};

void EnFireFlow_Init(Actor* thisx, PlayState* play) {
    EnFireFlow* this = (EnFireFlow*)thisx;
    
    // Initialize collision
    Collider_InitCylinder(play, &this->collider);
    Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);
    
    // Store initial position
    this->originalPos = this->actor.world.pos;
    
    // Initialize flow parameters
    this->flowSpeed = 2.0f;
    this->flowHeight = 100.0f;
    this->flowState = 0;
    this->timer = 0;
    
    // Set actor properties
    this->actor.flags |= ACTOR_FLAG_4;
    Actor_SetScale(&this->actor, 0.1f);
}

void EnFireFlow_Destroy(Actor* thisx, PlayState* play) {
    EnFireFlow* this = (EnFireFlow*)thisx;
    Collider_DestroyCylinder(play, &this->collider);
}

void EnFireFlow_Update(Actor* thisx, PlayState* play) {
    EnFireFlow* this = (EnFireFlow*)thisx;
    Player* player = GET_PLAYER(play);
    
    this->timer++;
    
    // Update collision
    Collider_UpdateCylinder(&this->actor, &this->collider);
    CollisionCheck_SetAT(play, &play->colChkCtx, &this->collider.base);
    CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
    
    // Flow movement pattern
    switch(this->flowState) {
        case 0: // Rising
            if (this->actor.world.pos.y < (this->originalPos.y + this->flowHeight)) {
                this->actor.world.pos.y += this->flowSpeed;
            } else {
                this->flowState = 1;
            }
            break;
            
        case 1: // Falling
            if (this->actor.world.pos.y > this->originalPos.y) {
                this->actor.world.pos.y -= this->flowSpeed;
            } else {
                this->flowState = 0;
            }
            break;
    }
    
    // Damage player on contact
    if (this->collider.base.atFlags & AT_HIT) {
        this->collider.base.atFlags &= ~AT_HIT;
        if (this->collider.base.at == &player->actor) {
            func_8002F71C(play, &this->actor, 8.0f, this->actor.yawTowardsPlayer, 8.0f);
            gSaveContext.health -= 8;
        }
    }
}

void EnFireFlow_Draw(Actor* thisx, PlayState* play) {
    EnFireFlow* this = (EnFireFlow*)thisx;
    
    OPEN_DISPS(play->state.gfxCtx);
    
    Gfx_SetupDL_25Opa(play->state.gfxCtx);
    gDPSetPrimColor(POLY_OPA_DISP++, 0, 0, 255, 50, 0, 255);
    
    Matrix_Push();
    Matrix_Translate(this->actor.world.pos.x, this->actor.world.pos.y, this->actor.world.pos.z, MTXMODE_NEW);
    Matrix_Scale(this->actor.scale.x, this->actor.scale.y, this->actor.scale.z, MTXMODE_APPLY);
    Matrix_RotateY(this->actor.world.rot.y * (M_PI / 32768.0f), MTXMODE_APPLY);
    
    gSPMatrix(POLY_OPA_DISP++, Matrix_NewMtx(play->state.gfxCtx, __FILE__, __LINE__), 
              G_MTX_MODELVIEW | G_MTX_LOAD | G_MTX_NOPUSH);
    
    Matrix_Pop();
    
    CLOSE_DISPS(play->state.gfxCtx);
}

const ActorProfile En_FireFlow_InitVars = {
    /**/ ACTOR_EN_FIREFLOW,
    /**/ ACTORCAT_PROP,
    /**/ FLAGS,
    /**/ OBJECT_GAMEPLAY_KEEP,
    /**/ sizeof(EnFireFlow),
    /**/ EnFireFlow_Init,
    /**/ EnFireFlow_Destroy,
    /**/ EnFireFlow_Update, 
    /**/ EnFireFlow_Draw
};