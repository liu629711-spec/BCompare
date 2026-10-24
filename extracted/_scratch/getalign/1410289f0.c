function: FUN_1410289f0
entry: 1410289f0
body_size: 139
signature: undefined FUN_1410289f0()


void FUN_1410289f0(longlong param_1,int param_2)

{
  undefined8 uVar1;
  undefined1 auStack_48 [40];
  undefined1 *local_20;
  longlong local_18;
  longlong local_10;
  
  local_20 = auStack_48;
  uVar1 = FUN_14102a280(param_1);
  FUN_140e64df0(uVar1);
  local_10 = *(longlong *)(param_1 + 0x48);
  local_18 = local_10;
  if (local_10 != 0) {
    local_18 = *(longlong *)(local_10 + -8);
  }
  if (local_18 < param_2) {
    FUN_140019870(param_1 + 0x48,PTR_DAT_14101e3e8,1,(longlong)param_2);
  }
  uVar1 = FUN_14102a280(param_1);
  FUN_140e66a40(uVar1);
  return;
}


