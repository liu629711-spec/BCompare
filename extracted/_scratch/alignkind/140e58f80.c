function: FUN_140e58f80
entry: 140e58f80
body_size: 629
signature: undefined FUN_140e58f80()


void FUN_140e58f80(undefined8 param_1)

{
  int iVar1;
  longlong lVar2;
  undefined8 uVar3;
  undefined1 auStack_98 [36];
  int local_74;
  int local_70;
  int local_6c;
  undefined8 local_68;
  undefined8 local_60;
  undefined8 local_58;
  undefined1 *local_50;
  longlong local_38;
  undefined8 local_30;
  int local_28;
  int local_24;
  longlong *local_20;
  
  local_50 = auStack_98;
  local_68 = 0;
  local_60 = 0;
  local_58 = 0;
  local_30 = 0;
  FUN_140dbe0c0();
  lVar2 = FUN_140e573a0();
  local_74 = *(int *)(lVar2 + 8) + -1;
  local_24 = 0;
  iVar1 = *(int *)(lVar2 + 8);
  if (-1 < local_74) {
    do {
      local_74 = iVar1;
      uVar3 = FUN_140e573a0();
      local_38 = FUN_140e57390(uVar3,local_24);
      iVar1 = (**(code **)(local_38 + 0xa8))();
      local_70 = iVar1 + -1;
      local_28 = 0;
      if (-1 < local_70) {
        do {
          local_70 = iVar1;
          local_20 = (longlong *)(**(code **)(local_38 + 0x18))(local_38,1);
          FUN_14067ed80(local_20,0,0);
          (**(code **)(*local_20 + 0xa0))(local_20,local_28);
          FUN_140014550(&local_30,L"Dummy");
          if (0 < local_28) {
            FUN_140044ba0(&local_58,local_28);
            FUN_140016090(&local_30,local_58);
          }
          FUN_1400104d0(*local_20,&local_60);
          uVar3 = FUN_140e5a140(param_1,local_60,local_30,1);
          (**(code **)(*local_20 + 0x28))(local_20,uVar3);
          FUN_140010870();
          local_28 = local_28 + 1;
          local_70 = local_70 + -1;
          iVar1 = local_70;
        } while (local_70 != 0);
      }
      local_24 = local_24 + 1;
      local_74 = local_74 + -1;
      iVar1 = local_74;
    } while (local_74 != 0);
  }
  lVar2 = FUN_140e573a0();
  local_6c = *(int *)(lVar2 + 8) + -1;
  local_24 = 0;
  iVar1 = *(int *)(lVar2 + 8);
  if (-1 < local_6c) {
    do {
      local_6c = iVar1;
      uVar3 = FUN_140e573a0();
      local_38 = FUN_140e57390(uVar3,local_24);
      local_20 = (longlong *)(**(code **)(local_38 + 0x18))(local_38,1);
      *(undefined1 *)(local_20 + 7) = 1;
      FUN_14067ed80(local_20,0,0);
      (**(code **)*local_20)(local_20);
      FUN_1400104d0(*local_20,&local_68);
      uVar3 = FUN_140e58680(param_1,local_68);
      (**(code **)(*local_20 + 0x28))(local_20,uVar3);
      FUN_140010870(local_20);
      local_24 = local_24 + 1;
      local_6c = local_6c + -1;
      iVar1 = local_6c;
    } while (local_6c != 0);
  }
  FUN_140013f10(&local_68,3);
  FUN_140013e30(&local_30);
  return;
}


