function: FUN_140e7d030
entry: 140e7d030
body_size: 160
signature: undefined FUN_140e7d030()


undefined8 FUN_140e7d030(undefined8 param_1)

{
  longlong lVar1;
  longlong local_20 [2];
  undefined8 local_10;
  
  local_20[0] = 0;
  local_10 = 0;
  if (DAT_141e8eea0 == 0) {
    lVar1 = FUN_140e7c680(PTR_PTR_140e7a5e8,1);
    if (lVar1 == 0) {
      lVar1 = 0;
    }
    else {
      lVar1 = lVar1 + 0x20;
    }
    FUN_14001c140(&local_10,lVar1);
    FUN_140e7d3e0(local_20,&DAT_141e8eea0,local_10,0);
    if (local_20[0] != 0) {
      FUN_14001c100(&local_10);
    }
  }
  FUN_14001c140(param_1,DAT_141e8eea0);
  FUN_14001c100(local_20);
  FUN_14001c100(&local_10);
  return param_1;
}


