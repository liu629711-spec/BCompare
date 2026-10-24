function: FUN_140e7cdc0
entry: 140e7cdc0
body_size: 160
signature: undefined FUN_140e7cdc0()


undefined8 FUN_140e7cdc0(undefined8 param_1)

{
  longlong lVar1;
  longlong local_20 [2];
  undefined8 local_10;
  
  local_20[0] = 0;
  local_10 = 0;
  if (DAT_141e8ee88 == 0) {
    lVar1 = FUN_140e7bed0(PTR_PTR_140e795d8,1);
    if (lVar1 == 0) {
      lVar1 = 0;
    }
    else {
      lVar1 = lVar1 + 0x20;
    }
    FUN_14001c140(&local_10,lVar1);
    FUN_140e7d3e0(local_20,&DAT_141e8ee88,local_10,0);
    if (local_20[0] != 0) {
      FUN_14001c100(&local_10);
    }
  }
  FUN_14001c140(param_1,DAT_141e8ee88);
  FUN_14001c100(local_20);
  FUN_14001c100(&local_10);
  return param_1;
}


