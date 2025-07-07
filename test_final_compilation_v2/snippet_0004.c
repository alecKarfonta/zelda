// Snippet 4
// Success: False
// Compilation time: 0.086s

typedef struct {
    /* 0x0000 */ Actor actor;
    /* 0x014C */ s16 timer;
    /* 0x014E */ s16 actionState; 
    /* 0x0150 */ f32 scale;
    /* 0x0154 */ ColliderCylinder collider;
} EnCrystal; // size = 0x1A0

void EnCrystal_Init(Actor* thisx, PlayState* play) {
    EnCrystal* this = (EnCrystal*)thisx;
    
    // Initialize collision using authentic pattern
    Collider_InitCylinder(play, &this->collider);
    Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);
    
    this->actor.gravity = -1.0f;
    this->actor.minVelocityY = -10.0f;
    Actor_SetScale(&this->actor, 0.01f);
    
    this->actionState = 0;
    this->timer = 0;
}

void EnCrystal_Update(Actor* thisx, PlayState* play) {
    EnCrystal* this = (EnCrystal*)thisx;
    Player* player = GET_PLAYER(play);
    
    // Update collision and physics
    Actor_UpdateBgCheckInfo(play, &this->actor, 20.0f, 20.0f, 0.0f, UPDBGCHECKINFO_FLAG_0 | UPDBGCHECKINFO_FLAG_2);
    Collider_UpdateCylinder(&this->actor, &this->collider);
    CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
    
    // Basic state machine
    switch(this->actionState) {
        case 0:
            if (Actor_WorldDistXZToActor(&this->actor, &player->actor) < 100.0f) {
                this->actionState = 1;
                this->timer = 20;
            }
            break;
            
        case 1:
            this->timer--;
            if (this->timer <= 0) {
                Actor_Kill(&this->actor);
            }
            break;
    }
    
    // Apply movement
    Actor_MoveXZGravity(&this->actor);
}

void EnCrystal_Draw(Actor* thisx, PlayState* play) {
    EnCrystal* this = (EnCrystal*)thisx;
    
    OPEN_DISPS(play->state.gfxCtx);
    
    Gfx_SetupDL_25Opa(play->state.gfxCtx);
    gSPMatrix(POLY_OPA_DISP++, Matrix_NewMtx(play->state.gfxCtx, __FILE__, __LINE__), 
              G_MTX_MODELVIEW | G_MTX_LOAD | G_MTX_NOPUSH);
    gSPDisplayList(POLY_OPA_DISP++, gCrystalDL);
    
    CLOSE_DISPS(play->state.gfxCtx);
}

const ActorProfile En_Crystal_InitVars = {
    /**/ ACTOR_EN_CRYSTAL,
    /**/ ACTORCAT_PROP,
    /**/ FLAGS,
    /**/ OBJECT_GAMEPLAY_KEEP,
    /**/ sizeof(EnCrystal),
    /**/ EnCrystal_Init,
    /**/ EnCrystal_Destroy,
    /**/ EnCrystal_Update,
    /**/ EnCrystal_Draw
};