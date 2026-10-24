function: FUN_1417a3830
entry: 1417a3830
body_size: 250
signature: undefined FUN_1417a3830()


void FUN_1417a3830(longlong param_1)

{
  longlong lVar1;
  undefined1 auStack_88 [32];
  undefined4 local_68;
  undefined4 local_60;
  undefined4 local_58;
  code *local_40;
  longlong local_38;
  undefined1 *local_30;
  undefined4 *local_28;
  byte local_19;
  undefined4 local_18 [2];
  undefined8 local_10;
  
  local_30 = auStack_88;
  FUN_140dd5230(param_1);
  if (*(longlong *)(param_1 + 0x158) == 0) {
    local_19 = 0;
    local_28 = local_18;
    do {
      lVar1 = *(longlong *)(param_1 + 0x138 + (ulonglong)local_19 * 8);
      if ((lVar1 == 0) || (*(char *)(lVar1 + 0xb0) == '\0')) {
        *local_28 = 0;
      }
      else {
        *local_28 = 1;
      }
      local_19 = local_19 + 1;
      local_28 = local_28 + 1;
    } while (local_19 != 2);
    local_10 = FUN_1417a5570(PTR_PTR_14179b2d0,1,param_1);
    local_40 = FUN_1417a4380;
    local_68 = local_18[1];
    local_60 = 0xffffffff;
    local_58 = 0xffffffff;
    local_38 = param_1;
    FUN_140e71a10(local_10,param_1,&local_40,local_18[0]);
    FUN_140010870(local_10);
  }
  return;
}


