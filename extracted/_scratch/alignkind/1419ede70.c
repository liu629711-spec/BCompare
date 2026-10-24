function: FUN_1419ede70
entry: 1419ede70
body_size: 145
signature: undefined FUN_1419ede70()


void FUN_1419ede70(longlong param_1,longlong param_2)

{
  char cVar1;
  undefined8 uVar2;
  undefined8 local_10;
  
  local_10 = 0;
  FUN_1419ed0a0(param_1,param_2);
  cVar1 = FUN_140010d70(param_2,PTR_PTR_1419e6358);
  if (cVar1 == '\0') {
    FUN_14001e690(&local_10,&LAB_1419e89c8);
    uVar2 = FUN_1406e3fc0(PTR_PTR_1419e5910,1,local_10);
    FUN_140012e10(uVar2);
  }
  *(undefined1 *)(param_1 + 0x38) = *(undefined1 *)(param_2 + 0x38);
  FUN_1400144c0(param_1 + 0x40,*(undefined8 *)(param_2 + 0x40));
  FUN_140013e30(&local_10);
  return;
}


