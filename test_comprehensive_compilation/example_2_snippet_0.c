// Parsed C code from example_2_snippet_0
// Extracted from training data

// Spirit Temple sand flow actor
typedef struct {
    /* 0x0000 */ Actor actor;
    /* 0x014C */ s16 timer;
    /* 0x014E */ s16 actionState;
    /* 0x0150 */ f32 sandHeight;
    /* 0x0154 */ f32 targetHeight;
    /* 0x0158 */ f32 flowSpeed;
    /* 0x015C */ Vec3f particlePos[16];
    /* 0x01FC */ s16 particleTimer[16];
    /* 0x021C */ ColliderCylinder collider;
} EnSandFlow; // size = 0x268

// Action states
#define SANDFLOW_STATE_IDLE 0
#define SANDFLOW_STATE_RISING 1
#define SANDFLOW_STATE_FALLING 2

static ColliderCylinderInit sCylinderInit = {
    {
        COLTYPE_NONE,
        AT_NONE,
        AC_ON | AC_TYPE_PLAYER,
        OC1_ON | OC1_TYPE_ALL,
        OC2_TYPE_1,
        COLSHAPE_CYLINDER,
    },
    {
        ELEMTYPE_UNK0,
        { 0x00000000, 0x00, 0x00 },
        { 0x00000008, 0x00, 0x00 },
        TOUCH_NONE,
        BUMP_ON,
        OCELEM_ON,
    },
    { 50, 100, 0, { 0, 0, 0 } },
};

void EnSandFlow_Init(Actor* thisx, PlayState* play) {
    EnSandFlow* this = (EnSandFlow*)thisx;
    s32 i;

    Actor_SetScale(&this->actor, 0.1f);
    
    // Initialize collision
    Collider_InitCylinder(play, &this->collider);
    Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);
    
    this->actionState = SANDFLOW_STATE_IDLE;
    this->sandHeight = this->actor.world.pos.y;
    this->targetHeight = this->sandHeight;
    this->flowSpeed = 0.0f;
    
    // Initialize particles
    for (i = 0; i < 16; i++) {
        this->particlePos[i] = this->actor.world.pos;
        this->particleTimer[i] = 0;
    }
}

void EnSandFlow_UpdateParticles(EnSandFlow* this) {
    s32 i;
    
    for (i = 0; i < 16; i++) {
        if (this->particleTimer[i] > 0) {
            this->particleTimer[i]--;
            this->particlePos[i].y += this->flowSpeed;
        } else if (Rand_ZeroOne() < 0.1f) {
            this->particlePos[i] = this->actor.world.pos;
            this->particlePos[i].x += Rand_CenteredFloat(30.0f);
            this->particlePos[i].z += Rand_CenteredFloat(30.0f);
            this->particleTimer[i] = 30;
        }
    }
}

void EnSandFlow_Update(Actor* thisx, PlayState* play) {
    EnSandFlow* this = (EnSandFlow*)thisx;
    Player* player = GET_PLAYER(play);
    
    this->timer++;
    
    switch (this->actionState) {
        case SANDFLOW_STATE_IDLE:
            if (Actor_WorldDistXZToActor(&this->actor, &player->actor) < 100.0f) {
                this->actionState = SANDFLOW_STATE_RISING;
                this->targetHeight = this->sandHeight + 200.0f;
                this->flowSpeed = 2.0f;
            }
            break;
            
        case SANDFLOW_STATE_RISING:
            Math_SmoothStepToF(&this->actor.world.pos.y, this->targetHeight, 0.3f, 3.0f, 0.1f);
            
            if (fabsf(this->actor.world.pos.y - this->targetHeight) < 1.0f) {
                this->actionState = SANDFLOW_STATE_FALLING;
                this->targetHeight = this->sandHeight;
                this->flowSpeed = -2.0f;
            }
            break;
            
        case SANDFLOW_STATE_FALLING:
            Math_SmoothStepToF(&this->actor.world.pos.y, this->targetHeight, 0.3f, 3.0f, 0.1f);
            
            if (fabsf(this->actor.world.pos.y - this->targetHeight) < 1.0f) {
                this->actionState = SANDFLOW_STATE_IDLE;
                this->flowSpeed = 0.0f;
            }
            break;
    }
    
    EnSandFlow_UpdateParticles(this);
    
    // Update collision
    Collider_UpdateCylinder(&this->actor, &this->collider);
    CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
}

void EnSandFlow_Draw(Actor* thisx, PlayState* play) {
    EnSandFlow* this = (EnSandFlow*)thisx;
    s32 i;
    
    OPEN_DISPS(play->state.gfxCtx);
    
    Gfx_SetupDL_25Opa(play->state.gfxCtx);
    
    gDPSetPrimColor(POLY_OPA_DISP++, 0, 0, 200, 170, 100, 255);
    
    Matrix_Push();
    Matrix_Translate(this->actor.world.pos.x, this->actor.world.pos.y, 
                    this->actor.world.pos.z, MTXMODE_NEW);
    Matrix_Scale(this->actor.scale.x, this->actor.scale.y, 
                this->actor.scale.z, MTXMODE_APPLY);
    Matrix_RotateY(this->actor.world.rot.y * (M_PI / 32768.0f), MTXMODE_APPLY);
    
    gSPMatrix(POLY_OPA_DISP++, Matrix_NewMtx(play->state.gfxCtx, __FILE__, __LINE__),
              G_MTX_MODELVIEW | G_MTX_LOAD | G_MTX_NOPUSH);
              
    Matrix_Pop();
    
    // Draw particles
    for (i = 0; i < 16; i++) {
        if (this->particleTimer[i] > 0) {
            Matrix_Push();
            Matrix_Translate(this->particlePos[i].x, this->particlePos[i].y,
                           this->particlePos[i].z, MTXMODE_NEW);
            Matrix_Scale(0.2f, 0.2f, 0.2f, MTXMODE_APPLY);
            
            gSPMatrix(POLY_OPA_DISP++, 
                     Matrix_NewMtx(play->state.gfxCtx, __FILE__, __LINE__),
                     G_MTX_MODELVIEW | G_MTX_LOAD | G_MTX_NOPUSH);
            Matrix_Pop();
        }
    }
    
    CLOSE_DISPS(play->state.gfxCtx);
}

const ActorProfile En_SandFlow_InitVars = {
    /**/ ACTOR_EN_SANDFLOW,
    /**/ ACTORCAT_PROP,
    /**/ FLAGS_0,
    /**/ OBJECT_GAMEPLAY_KEEP,
    /**/ sizeof(EnSandFlow),
    /**/ EnSandFlow_Init,
    /**/ Actor_Destroy,
    /**/ EnSandFlow_Update,
    /**/ EnSandFlow_Draw
};