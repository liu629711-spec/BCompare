function: FUN_140e733b0
entry: 140e733b0
body_size: 840
signature: undefined FUN_140e733b0()


void FUN_140e733b0(longlong param_1,int param_2,int param_3,int *param_4,int *param_5,
                  undefined1 param_6)

{
  int iVar1;
  undefined1 auStack_88 [32];
  int *local_68;
  undefined1 local_60;
  undefined1 *local_50;
  int local_44;
  int local_40;
  int local_3c;
  int local_38;
  int local_30;
  int local_2c;
  int local_28;
  
  local_50 = auStack_88;
  local_38 = param_2 + *(int *)(param_1 + 0x98) + -1;
  local_3c = local_38;
  if (*param_4 <= local_38) {
    local_3c = *param_4;
  }
  *param_4 = local_3c;
  local_40 = param_3 + *(int *)(param_1 + 0x98) + -1;
  local_44 = local_40;
  if (*param_5 <= local_40) {
    local_44 = *param_5;
  }
  *param_5 = local_44;
  *(int *)(param_1 + 0x84) = (*param_4 - param_2) + 1;
  *(int *)(param_1 + 0x5c) = (*param_5 - param_3) + 1;
  *(undefined4 *)(param_1 + 0x88) = 0;
  FUN_140019870(param_1 + 0xa0,PTR_DAT_140e71488,1,(longlong)(*(int *)(param_1 + 0x84) + 1));
  *(int *)(param_1 + 0x9c) = param_2;
  *(int *)(param_1 + 0xa8) = param_3;
  local_2c = param_3;
  local_28 = param_2;
  FUN_140e72330(param_1,param_2 - *(int *)(param_1 + 0x9c));
  FUN_140e73040(auStack_88,local_28,local_2c);
  do {
    FUN_140e722a0(param_1,1,local_2c + 1,param_5);
    FUN_140e722a0(param_1,0,local_28 + 1,param_4);
    if (local_2c + 1 <= *param_5) {
      local_2c = local_2c + 1;
    }
    if (local_28 + 1 <= *param_4) {
      local_28 = local_28 + 1;
      FUN_140e72330(param_1,local_28 - *(int *)(param_1 + 0x9c));
    }
    local_30 = local_28;
    if (param_2 <= local_28) {
      iVar1 = (param_2 - local_28) + -1;
      do {
        FUN_140e73040(auStack_88,local_30,local_2c);
        local_30 = local_30 + -1;
        iVar1 = iVar1 + 1;
      } while (iVar1 != 0);
    }
    local_30 = local_2c + -1;
    if (param_3 <= local_30) {
      iVar1 = (param_3 - local_30) + -1;
      do {
        FUN_140e73040(auStack_88,local_28,local_30);
        local_30 = local_30 + -1;
        iVar1 = iVar1 + 1;
      } while (iVar1 != 0);
    }
    FUN_140ddfb30(*(undefined8 *)(param_1 + 8));
  } while ((local_28 < *param_4) || (local_2c < *param_5));
  local_68 = param_5;
  local_60 = param_6;
  FUN_140e74100(param_1,param_2,param_3,param_4);
  FUN_140019a50(param_1 + 0x90,PTR_DAT_140e713e8);
  FUN_140019a50(param_1 + 0xa0,PTR_DAT_140e71488);
  return;
}


