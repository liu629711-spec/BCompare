function: FUN_14102b660
entry: 14102b660
body_size: 691
signature: undefined FUN_14102b660()


void FUN_14102b660(longlong param_1,longlong param_2)

{
  int iVar1;
  undefined1 auStack_b8 [32];
  int local_98;
  int local_90;
  uint local_88;
  ulonglong local_78;
  code *local_70;
  longlong local_68;
  undefined1 *local_60;
  longlong *local_58;
  undefined8 *local_50;
  byte local_3e;
  byte local_3d;
  int local_3c;
  int local_38;
  int local_34;
  longlong *local_30;
  char local_21;
  undefined8 local_20;
  
  local_60 = auStack_b8;
  local_3e = *(byte *)(param_2 + 0x90);
  local_78 = (ulonglong)local_3e;
  local_3d = PTR_DAT_141fb2d98[local_78];
  local_21 = '\x01';
  local_50 = *(undefined8 **)(param_1 + 0x118);
  (**(code **)*local_50)(local_50);
  local_34 = *(int *)(param_1 + 0x124 + local_78 * 4);
  iVar1 = *(int *)(param_1 + 0x124 + (ulonglong)local_3d * 4);
  if ((local_34 < iVar1) &&
     (*(int *)(*(longlong *)(param_1 + 0x130) + 8 + (longlong)local_34 * 0xc) < 0)) {
    local_38 = *(int *)(*(longlong *)(param_1 + 0x130) + (longlong)local_34 * 0xc +
                       (ulonglong)local_3d * 4);
    local_34 = local_34 + 1;
    iVar1 = iVar1 + -1;
    local_3c = local_38;
    if (local_34 <= iVar1) {
      iVar1 = (iVar1 - local_34) + 1;
      do {
        if (-1 < *(int *)(*(longlong *)(param_1 + 0x130) + 8 + (longlong)local_34 * 0xc)) break;
        local_3c = local_3c + 1;
        local_34 = local_34 + 1;
        iVar1 = iVar1 + -1;
      } while (iVar1 != 0);
    }
    local_58 = *(longlong **)(param_1 + 0x118);
    (**(code **)(*local_58 + 8))(local_58);
    local_21 = '\0';
    local_98 = CONCAT31(local_98._1_3_,local_3e);
    local_20 = FUN_14102c200(PTR_LAB_141020f20,1,*(undefined8 *)(param_1 + 0xe8),local_3d);
    local_70 = FUN_14102adc0;
    local_98 = *(int *)(param_1 + 0x138 + (ulonglong)local_3e * 4);
    local_90 = local_3c;
    local_88 = (local_98 + *(int *)(param_1 + 0xf0 + (ulonglong)local_3e * 4)) - 1;
    local_68 = param_1;
    FUN_140e71a10(local_20,param_2,&local_70,local_38);
    FUN_140010870(local_20);
  }
  else {
    local_98 = *(int *)(param_1 + 0x138 + (ulonglong)local_3e * 4);
    local_90 = *(int *)(param_1 + 0xf0 + (ulonglong)local_3e * 4);
    local_88 = local_88 & 0xffffff00;
    FUN_14102af70(param_1,2,local_3e,0xffffffff);
  }
  if (local_21 != '\0') {
    local_30 = *(longlong **)(param_1 + 0x118);
    (**(code **)(*local_30 + 8))(local_30);
  }
  return;
}


