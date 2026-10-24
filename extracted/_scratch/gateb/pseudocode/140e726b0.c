function: FUN_140e726b0
entry: 140e726b0
body_size: 984
signature: undefined FUN_140e726b0()


int FUN_140e726b0(longlong param_1,undefined4 param_2,undefined4 param_3)

{
  int iVar1;
  int iVar2;
  undefined1 auStack_a8 [40];
  undefined8 local_80;
  undefined8 local_78;
  undefined1 *local_70;
  int local_60;
  int local_5c;
  int local_58;
  int local_54;
  int local_50;
  int local_4c;
  int local_48;
  int local_44;
  int local_40;
  int local_3c;
  int local_38;
  int local_34;
  longlong local_30;
  longlong local_28;
  int local_1c;
  
  local_70 = auStack_a8;
  local_80 = 0;
  local_78 = 0;
  local_28 = 0;
  local_30 = 0;
  iVar1 = FUN_140e72e80(param_1,0,param_2);
  iVar2 = FUN_140e72e80(param_1,1,param_3);
  if (iVar1 == iVar2) {
    (**(code **)(**(longlong **)(param_1 + 0x10) + 0x50))(*(longlong **)(param_1 + 0x10));
    (**(code **)(**(longlong **)(param_1 + 0x10) + 0x40))
              (*(longlong **)(param_1 + 0x10),&local_78,0,param_2);
    FUN_140015490(&local_28,local_78,0xfde9);
    (**(code **)(**(longlong **)(param_1 + 0x10) + 0x40))
              (*(longlong **)(param_1 + 0x10),&local_80,1,param_3);
    FUN_140015490(&local_30,local_80,0xfde9);
    (**(code **)(**(longlong **)(param_1 + 0x10) + 0x58))(*(longlong **)(param_1 + 0x10));
    if ((local_28 == 0) || (local_30 == 0)) {
      local_1c = -10;
    }
    else {
      iVar1 = FUN_140e74a70(param_1,0,param_2);
      iVar2 = FUN_140e74a70(param_1,1,param_3);
      local_1c = (iVar1 + iVar2) * 2;
      local_34 = 0;
      if (local_28 != 0) {
        local_34 = *(int *)(local_28 + -4);
      }
      local_38 = 0;
      if (local_30 != 0) {
        local_38 = *(int *)(local_30 + -4);
      }
      if (local_34 != local_38) {
        local_1c = local_1c + -1;
      }
    }
  }
  else if (*(char *)(param_1 + 0xac) == '\0') {
    if (*(char *)(param_1 + 0x80) == '\0') {
      local_1c = -0x12;
    }
    else {
      local_1c = -5000;
    }
  }
  else {
    FUN_140e723a0(auStack_a8,0,param_2,&local_28);
    FUN_140e723a0(auStack_a8,1,param_3,&local_30);
    if ((local_28 == 0) || (local_30 == 0)) {
      if (*(char *)(param_1 + 0x58) == '\0') {
        local_3c = 0;
        if (local_28 != 0) {
          local_3c = *(int *)(local_28 + -4);
        }
        local_40 = 0;
        if (local_30 != 0) {
          local_40 = *(int *)(local_30 + -4);
        }
        local_44 = (local_3c + local_40) * -4 + -1;
        if (-0xc < local_44) {
          local_44 = -0xb;
        }
        if (local_44 < -0x27) {
          local_48 = -0x28;
        }
        else {
          local_48 = local_44;
        }
        local_1c = local_48;
      }
      else {
        local_1c = -0x12;
      }
    }
    else {
      local_1c = FUN_140e725f0(auStack_a8,local_28,local_30);
      if (*(char *)(param_1 + 0x58) == '\0') {
        local_4c = 0;
        if (local_28 != 0) {
          local_4c = *(int *)(local_28 + -4);
        }
        local_50 = 0;
        if (local_30 != 0) {
          local_50 = *(int *)(local_30 + -4);
        }
        iVar1 = (local_1c * 3 - local_4c) - local_50;
        if (iVar1 < 1) {
          local_60 = iVar1 * 4 + -1;
          if (local_60 < -0x27) {
            local_60 = -0x28;
          }
          local_1c = local_60;
        }
        else {
          local_54 = 0;
          if (local_28 != 0) {
            local_54 = *(int *)(local_28 + -4);
          }
          local_58 = 0;
          if (local_30 != 0) {
            local_58 = *(int *)(local_30 + -4);
          }
          if (local_54 < local_58) {
            local_5c = local_54;
          }
          else {
            local_5c = local_58;
          }
          local_1c = (iVar1 * 0x19) / local_5c;
        }
      }
    }
  }
  FUN_140013f10(&local_80,2);
  FUN_140013f60(&local_30,2);
  return local_1c;
}


