# Overlay wrappers vs SCAR natives

SIM_BLOCK=1341 FOW_ON=20 FOW_OFF=10

## wrap_timerule (67)

AOE4HOOK_Local TimeRule (no Insert)

- `ConditionalRule_ExistsWithID`
- `ConditionalRule_Remove`
- `ConditionalRule_RemoveAll`
- `ConditionalRule_RemoveWithID`
- `Rule_Add`
- `Rule_AddInterval`
- `Rule_AddIntervalWithDelay`
- `Rule_AddOneShot`
- `Rule_ChangeInterval`
- `Rule_ChangeIntervalWithID`
- `Rule_Exists`
- `Rule_ExistsWithID`
- `Rule_GetInterval`
- `Rule_GetIntervalWithID`
- `Rule_GetTime`
- `Rule_GetTimeWithID`
- `Rule_GroupCount`
- `Rule_Pause`
- `Rule_PauseAll`
- `Rule_PauseWithID`
- `Rule_Refresh`
- `Rule_Remove`
- `Rule_RemoveAll`
- `Rule_RemoveMe`
- `Rule_RemoveWithID`
- `Rule_Replace`
- `Rule_ReplaceWithID`
- `Rule_TimerUpdate`
- `Rule_Unpause`
- `Rule_UnpauseAll`
- `Rule_UnpauseWithID`
- `TimeRule_Add`
- `TimeRule_AddData`
- `TimeRule_AddInterval`
- `TimeRule_AddIntervalData`
- `TimeRule_AddIntervalEx`
- `TimeRule_AddIntervalExData`
- `TimeRule_AddOneShot`
- `TimeRule_AddOneShotData`
- `TimeRule_ChangeInterval`
- `TimeRule_ChangeIntervalWithID`
- `TimeRule_Exists`
- `TimeRule_ExistsWithID`
- `TimeRule_GetCurrentTime`
- `TimeRule_GetCurrentTimeWithID`
- `TimeRule_GetInterval`
- `TimeRule_GetIntervalWithID`
- `TimeRule_Pause`
- `TimeRule_PauseAll`
- `TimeRule_PauseWithGroup`
- `TimeRule_PauseWithID`
- `TimeRule_Refresh`
- `TimeRule_Remove`
- `TimeRule_RemoveAll`
- `TimeRule_RemoveMe`
- `TimeRule_RemoveWithID`
- `TimeRule_Replace`
- `TimeRule_ReplaceWithID`
- `TimeRule_Unpause`
- `TimeRule_UnpauseAll`
- … +7 in CHECKSUM_MATRIX.tsv

## wrap_eventrule (58)

AOE4HOOK_Local EventRule + WORLD_DATA

- `EGroup_NotifyOnPlayerDemolition`
- `Entity_NotifyOnPlayerDemolition`
- `EventRule_AddEntityEvent`
- `EventRule_AddEntityEventData`
- `EventRule_AddEvent`
- `EventRule_AddEventData`
- `EventRule_AddEventFilter_EntityBlueprint`
- `EventRule_AddEventFilter_EntityPlayerOwner`
- `EventRule_AddEventFilter_EntityType`
- `EventRule_AddEventFilter_StateModelBool`
- `EventRule_AddPlayerEvent`
- `EventRule_AddPlayerEventData`
- `EventRule_AddSquadEvent`
- `EventRule_AddSquadEventData`
- `EventRule_Exists`
- `EventRule_GetNextUniqueRuleID`
- `EventRule_Pause`
- `EventRule_PauseAll`
- `EventRule_Refresh`
- `EventRule_RemoveAll`
- `EventRule_RemoveEntityEvent`
- `EventRule_RemoveEvent`
- `EventRule_RemoveMe`
- `EventRule_RemovePlayerEvent`
- `EventRule_RemoveRuleIDEvent`
- `EventRule_RemoveSquadEvent`
- `EventRule_Unpause`
- `EventRule_UnpauseAll`
- `Event_CreateAND`
- `Event_Death`
- `Event_EncounterCanSeePlayerSquads`
- `Event_GroupCount`
- `Event_GroupIsDeadOrRetreating`
- `Event_GroupLeftAlive`
- `Event_IsEngaged`
- `Event_IsOutOfCombat`
- `Event_IsSelected`
- `Event_IsUnderAttack`
- `Event_PlayerCanSeeElement`
- `Event_SGroupCountMember`
- `Rule_AddEGroupEvent`
- `Rule_AddEntityEvent`
- `Rule_AddEventFilter_EntityBlueprint`
- `Rule_AddEventFilter_EntityPlayerOwner`
- `Rule_AddEventFilter_EntityType`
- `Rule_AddEventFilter_StateModelBool`
- `Rule_AddGlobalEvent`
- `Rule_AddPlayerEvent`
- `Rule_AddSGroupEvent`
- `Rule_AddSquadEvent`
- `Rule_RemoveEGroupEvent`
- `Rule_RemoveEntityEvent`
- `Rule_RemoveGlobalEvent`
- `Rule_RemovePlayerEvent`
- `Rule_RemoveSGroupEvent`
- `Rule_RemoveSquadEvent`
- `UnsavedEventRule_AddPlayerEvent`
- `UnsavedEventRule_AddRuleIDEvent`

## wrap_proximity (7)

AOE4HOOK_Local proximity poll

- `Event_EnterProximity`
- `Event_ExitProximity`
- `Event_Proximity`
- `Event_WhileInProximity`
- `Rule_EnterProximity`
- `Rule_ExitProximity`
- `Rule_WhileInProximity`

## wrap_fow_sim (32)

Guarded one-shot FOW debug (`getgametype` / replay); multiplayer and unknown modes no-op.

- `ChatCheatFOW`
- `CheatExploredAll`
- `CheatFoW`
- `FOW_Enable`
- `FOW_ExploreAll`
- `FOW_ForceRevealAllUnblockedAreas`
- `FOW_PlayerExploreAll`
- `FOW_PlayerRevealAll`
- `FOW_PlayerRevealArea`
- `FOW_PlayerRevealSGroup`
- `FOW_PlayerUnExploreAll`
- `FOW_PlayerUnRevealAll`
- `FOW_PlayerUnRevealArea`
- `FOW_PlayerUnRevealSGroup`
- `FOW_RevealAll`
- `FOW_RevealArea`
- `FOW_RevealEGroup`
- `FOW_RevealEGroupOnly`
- `FOW_RevealEntity`
- `FOW_RevealMarker`
- `FOW_RevealSGroup`
- `FOW_RevealSGroupOnly`
- `FOW_RevealSquad`
- `FOW_RevealTerritory`
- `FOW_Toggle`
- `FOW_UnExploreAll`
- `FOW_UnRevealAll`
- `FOW_UnRevealArea`
- `FOW_UnRevealMarker`
- `FOW_UnRevealTerritory`
- `FOW_UndoForceRevealAllUnblockedAreas`
- `Misc_RevealAllFOWTransition`

## sim_command (119)

MP_SAFE no-op (command stream)

- `Cmd_AbandonTeamWeapon`
- `Cmd_Ability`
- `Cmd_AttachSquads`
- `Cmd_Attack`
- `Cmd_AttackMove`
- `Cmd_AttackMoveThenCapture`
- `Cmd_CaptureTeamWeapon`
- `Cmd_Construct`
- `Cmd_DetonateDemolitions`
- `Cmd_DoPlan`
- `Cmd_EjectOccupants`
- `Cmd_FormationAttackMove`
- `Cmd_FormationMove`
- `Cmd_FormationMoveToAndDestroy`
- `Cmd_FormationStop`
- `Cmd_Garrison`
- `Cmd_HoldPosition`
- `Cmd_InstantReinforceUnit`
- `Cmd_InstantSetupTeamWeapon`
- `Cmd_InstantUpgrade`
- `Cmd_Move`
- `Cmd_MoveAwayFromPos`
- `Cmd_MoveToAndDeSpawn`
- `Cmd_MoveToAndDestroy`
- `Cmd_MoveToClosestMarker`
- `Cmd_MoveToThenAttackMove`
- `Cmd_MoveToThenCapture`
- `Cmd_RecrewVehicle`
- `Cmd_ReinforceUnit`
- `Cmd_Retreat`
- `Cmd_RevertOccupiedBuilding`
- `Cmd_SetDemolitions`
- `Cmd_SetupTeamWeapon`
- `Cmd_SquadCamouflageStance`
- `Cmd_SquadPath`
- `Cmd_SquadPatrolMarker`
- `Cmd_StaggeredRetreat`
- `Cmd_Stop`
- `Cmd_StopSquadsExcept`
- `Cmd_Surrender`
- `Cmd_UngarrisonSquad`
- `Cmd_Upgrade`
- `Cmd_WalkToAndThenRun`
- `Command_PlayerBroadcastMessage`
- `LocalCommand_BeginSendingSquadCommandsAsFormation`
- `LocalCommand_EndSendingSquadCommandsAsFormation`
- `LocalCommand_Entity`
- `LocalCommand_EntityAbility`
- `LocalCommand_EntityBuildSquad`
- `LocalCommand_EntityEntity`
- `LocalCommand_EntityExt`
- `LocalCommand_EntityPos`
- `LocalCommand_EntityPosAbility`
- `LocalCommand_EntityPosDirAbility`
- `LocalCommand_EntityPosSquad`
- `LocalCommand_EntitySquad`
- `LocalCommand_EntityTargetEntityAbility`
- `LocalCommand_EntityTargetSquadAbility`
- `LocalCommand_EntityUpgrade`
- `LocalCommand_Init`
- … +59 in CHECKSUM_MATRIX.tsv

## sim_write (714)

MP_SAFE no-op (sim write)

- `AddPendingDissolve`
- `AddPendingUpdate`
- `AddTagsToElements`
- `AddVectorToPosition`
- `AutoTest_SaveLoadTestSetupDone`
- `CampaignAutotest_SetCheckpointStatus`
- `Cardinal_EnablePartialXboxUI`
- `ChatCheatAgeUpMultiplayer`
- `ChatCheatDestroySelected`
- `ChatCheatInstantBuildAndGather`
- `ChatCheatInvulnerable`
- `CheatAgeUpMultiplayer`
- `CheatConvertSelectedUnits`
- `CheatDestroySelected`
- `CheatEconomy`
- `CheatInstantBuildAndGather`
- `CheatInvulnerable`
- `CheatKillAllGaia`
- `CheatLoseInstantly`
- `CheatMenu_ActivateMenuItem`
- `CheatMenu_AddMenuItem`
- `CheatMenu_AddMenuItem_Event`
- `CheatMenu_GetValues`
- `CheatMenu_Init`
- `CheatMenu_IsSet`
- `CheatMenu_OverrideCheatFunction`
- `CheatMenu_RegisterCheatFunction`
- `CheatMenu_RestartGame`
- `CheatMenu_RestoreMenuItems`
- `CheatMenu_SetValues`
- `CheatMenu_StartWithCheat`
- `CheatReplaceSheepWithWolves`
- `CheatSetCurrentPopCapToMax`
- `CheatSetFireToBuildings`
- `CheatSlow`
- `CheatSpawnCoreUnits`
- `CheatTeleportSelected`
- `CheatTeleportSelectedSquads`
- `CheatTurbo`
- `Cheat_Callback`
- `Cheat_GrantAllRibbonsAndMedals`
- `Cheat_Init`
- `Cheat_ResetAchievementProgress`
- `ClearProductionQueueForEGroup`
- `ClearProductionQueueForEntity`
- `Core_AddPlayerToTeam`
- `Core_DelayedGameOver`
- `Core_DelayedSetPlayerDefeated`
- `Core_DelayedSetPlayerVictorious`
- `Core_OnGameOver`
- `Core_RemovePlayerFromPlayersTable`
- `Core_RevealFOWOnEliminationEnabled`
- `Core_SetDefaultDefeatPresentation`
- `Core_SetDefaultVictoriousPresentation`
- `Core_SetMutualPlayerRelationship`
- `Core_SetMutualRelationship`
- `Core_SetPlayerDefeated`
- `Core_SetPlayerVictorious`
- `Core_SetPostGameState`
- `Core_SetTeamDefeated`
- … +654 in CHECKSUM_MATRIX.tsv
