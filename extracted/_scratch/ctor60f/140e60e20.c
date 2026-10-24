function: FUN_140e60e20
entry: 140e60e20
body_size: 234
signature: undefined FUN_140e60e20()


char FUN_140e60e20(longlong *param_1,longlong param_2)

{
  char cVar1;
  int iVar2;
  int iVar3;
  longlong local_20;
  
  local_20 = 0;
  if (*(char *)(param_1[9] + 0x14d) != '\x01') {
    cVar1 = FUN_1405f3780(param_2);
    if (cVar1 == '\0') {
      cVar1 = '\0';
      goto LAB_140e60e5f;
    }
  }
  cVar1 = '\x01';
LAB_140e60e5f:
  if ((cVar1 == '\0') && (param_1[0xd] == 0)) {
    FUN_140014550(&local_20,*(undefined8 *)(param_2 + 8));
    if (local_20 == 0) {
      FUN_14001e690(&local_20,&LAB_140e54150);
    }
    FUN_1400144c0(param_1 + 0xd,local_20);
    iVar2 = (**(code **)(*param_1 + 200))();
    iVar3 = 0;
    if (-1 < iVar2) {
      iVar2 = iVar2 + 1;
      do {
        FUN_140e62ea0(param_1,iVar3,0);
        iVar3 = iVar3 + 1;
        iVar2 = iVar2 + -1;
      } while (iVar2 != 0);
    }
    *(undefined1 *)((longlong)param_1 + 0x72) = 1;
  }
  FUN_140013e30(&local_20);
  return cVar1;
}


