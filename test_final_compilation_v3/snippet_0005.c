// Snippet 5
// Success: False
// Compilation time: 0.099s

// Spirit that steals items and mimics player actions
typedef struct {
    /* 0x0000 */ Actor actor;
    /* 0x014C */ SkelAnime skelAnime;
    /* 0x0190 */ Vec3s jointTable[25];
    /* 0x01F4 */ Vec3s morphTable[25];
    /* 0x0258 */ s16 actionState;
    /* 0x025A */ s16 actionTimer;
    /* 0x025C */ s16 stolenItem;
    /* 0x025E */ s16 attackTimer;
    /* 0x0260 */ f32 targetY;
    /* 0x0264 */ Vec3f lightningPos[8];
    /* 0x02C4 */ ColliderCylinder collider;
} EnSpiritThief;

// Collision initialization values
static ColliderCylinderInit sCylinderInit = {
    {
        COLTYPE_HIT0,
        AT_ON | AT_TYPE_ENEMY,
        AC_ON | AC_TYPE_PLAYER,
        OC1_ON | OC1_TYPE_ALL,
        OC2_TYPE_1,
        COLSHAPE_CYLINDER,
    },
    {
        ELEMTYPE_UNK0,
        { 0xFFCFFFFF, 0x00, 0x04 },
        { 0xFFCFFFFF, 0x00, 0x00 },
        TOUCH_ON | TOUCH_SFX_NONE,
        BUMP_ON,
        OCELEM_ON,
    },
    { 25, 45, 0, { 0, 0, 0 } },
};

void EnSpiritThief_Init(Actor* thisx, PlayState* play) {
    EnSpiritThief* this = (EnSpiritThief*)thisx;
    
    Actor_SetScale(&this->actor, 0.01f);
    SkelAnime_InitFlex(play, &this->skelAnime, &gGhostSkel, &gGhostFloatAnim, 
                       this->jointTable, this->morphTable, 25);
    
    Collider_InitCylinder(play, &this->collider);
    Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);
    
    this->actionState = 0;
    this->stolenItem = -1;
    this->actor.gravity = -1.0f;
    this->targetY = this->actor.world.pos.y;
}

void EnSpiritThief_StealItem(EnSpiritThief* this, PlayState* play) {
    Player* player = GET_PLAYER(play);
    
    // Check if close enough to steal
    if (Actor_WorldDistXZToActor(&this->actor, &player->actor) < 100.0f) {
        // Get currently equipped item
        s16 item = gSaveContext.equips.buttonItems[1];
        
        if (item != ITEM_NONE) {
            this->stolenItem = item;
            // Temporarily remove item from inventory
            gSaveContext.equips.buttonItems[1] = ITEM_NONE;
            // Play steal effect/sound
            Audio_PlayActorSound2(&this->actor, NA_SE_EN_STAL_DAMAGE);
        }
    }
}

void EnSpiritThief_Update(Actor* thisx, PlayState* play) {
    EnSpiritThief* this = (EnSpiritThief*)thisx;
    Player* player = GET_PLAYER(play);
    
    // Update collision
    Collider_UpdateCylinder(&this->actor, &this->collider);
    CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
    
    switch(this->actionState) {
        case 0: // Chase player
            Math_SmoothStepToF(&this->actor.world.pos.x, player->actor.world.pos.x, 
                              0.3f, 5.0f, 0.0f);
            Math_SmoothStepToF(&this->actor.world.pos.z, player->actor.world.pos.z, 
                              0.3f, 5.0f, 0.0f);
            
            // Float up/down
            this->targetY = this->actor.world.pos.y + Math_SinS(this->actionTimer * 0x800) * 10.0f;
            Math_SmoothStepToF(&this->actor.world.pos.y, this->targetY, 0.3f, 3.0f, 0.0f);
            
            if (!this->stolenItem) {
                EnSpiritThief_StealItem(this, play);
            }
            break;
            
        case 1: // Use stolen item
            if (this->stolenItem != -1) {
                // Use item logic here
                this->attackTimer--;
                if (this->attackTimer <= 0) {
                    // Return item
                    gSaveContext.equips.buttonItems[1] = this->stolenItem;
                    this->stolenItem = -1;
                    this->actionState = 0;
                }
            }
            break;
    }
    
    this->actionTimer++;
    SkelAnime_Update(&this->skelAnime);
    
    // Check if hit
    if (this->collider.base.acFlags & AC_HIT) {
        // Return stolen item if hit
        if (this->stolenItem != -1) {
            gSaveContext.equips.buttonItems[1] = this->stolenItem;
        }
        Actor_Kill(&this->actor);
    }
}

void EnSpiritThief_Draw(Actor* thisx, PlayState* play) {
    EnSpiritThief* this = (EnSpiritThief*)thisx;
    
    OPEN_DISPS(play->state.gfxCtx);
    
    Gfx_SetupDL_25Opa(play->state.gfxCtx);
    
    // Draw lightning effects
    if (this->stolenItem != -1) {
        Matrix_Push();
        // Draw lightning particles
        Matrix_Pop();
    }
    
    // Draw ghost model
    SkelAnime_DrawFlexOpa(play, this->skelAnime.skeleton, this->skelAnime.jointTable,
                          this->skelAnime.dListCount, NULL, NULL, this);
    
    CLOSE_DISPS(play->state.gfxCtx);
}

const ActorProfile En_SpiritThief_InitVars = {
    /**/ ACTOR_EN_SPIRIT_THIEF,
    /**/ ACTORCAT_ENEMY,
    /**/ FLAGS,
    /**/ OBJECT_GHOST,
    /**/ sizeof(EnSpiritThief),
    /**/ EnSpiritThief_Init,
    /**/ EnSpiritThief_Destroy,
    /**/ EnSpiritThief_Update,
    /**/ EnSpiritThief_Draw
};