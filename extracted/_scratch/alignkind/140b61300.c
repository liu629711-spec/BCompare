function: FUN_140b61300
entry: 140b61300
body_size: 225
signature: undefined FUN_140b61300()


void FUN_140b61300(longlong param_1)

{
  undefined8 local_20 [2];
  
  local_20[0] = 0;
  *(undefined8 *)(param_1 + 0x10) = 0;
  *(undefined8 *)(param_1 + 8) = 0;
  *(undefined1 *)(param_1 + 0x39) = 0;
  (**(code **)(**(longlong **)(param_1 + 0x20) + 0xd0))(*(longlong **)(param_1 + 0x20));
  *(undefined8 *)(param_1 + 0x28) = 0;
  *(undefined8 *)(param_1 + 0x30) = 0;
  *(undefined1 *)(param_1 + 0x38) = 3;
  FUN_1406c9bc0(param_1 + 0x18);
  *(undefined1 *)(param_1 + 0x88) = 0;
  *(undefined8 *)(param_1 + 0x80) = 0;
  *(undefined8 *)(param_1 + 0x90) = 0;
  FUN_1406c9ba0(local_20);
  FUN_140019af0(param_1 + 0x98,local_20[0],PTR_DAT_1406e61b0);
  if (*(char *)(param_1 + 0x78) == '\0') {
    *(undefined8 *)(param_1 + 0x70) = 0;
  }
  else {
    FUN_1406c9bc0(param_1 + 0x70);
  }
  FUN_140019a50(local_20,PTR_DAT_1406e61b0);
  return;
}


