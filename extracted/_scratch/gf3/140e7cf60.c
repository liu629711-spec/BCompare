function: FUN_140e7cf60
entry: 140e7cf60
body_size: 160
signature: undefined FUN_140e7cf60()


undefined8 FUN_140e7cf60(undefined8 param_1)

{
  longlong lVar1;
  longlong local_20 [2];
  undefined8 local_10;
  
  local_20[0] = 0;
  local_10 = 0;
  if (DAT_141e8ee98 == 0) {
    lVar1 = FUN_140e7c8f0(PTR_LAB_140e7a8e0,1);
    if (lVar1 == 0) {
      lVar1 = 0;
    }
    else {
      lVar1 = lVar1 + 0x20;
    }
    FUN_14001c140(&local_10,lVar1);
    FUN_140e7d3e0(local_20,&DAT_141e8ee98,local_10,0);
    if (local_20[0] != 0) {
      FUN_14001c100(&local_10);
    }
  }
  FUN_14001c140(param_1,DAT_141e8ee98);
  FUN_14001c100(local_20);
  FUN_14001c100(&local_10);
  return param_1;
}


