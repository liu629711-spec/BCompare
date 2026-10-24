function: FUN_140e72230
entry: 140e72230
body_size: 79
signature: undefined FUN_140e72230()


void FUN_140e72230(longlong param_1,longlong param_2)

{
  int iVar1;
  byte bVar2;
  int *piVar3;
  int local_10 [2];
  
  bVar2 = 0;
  piVar3 = local_10;
  do {
    iVar1 = *(int *)(param_2 + (longlong)(char)bVar2 * 4);
    *piVar3 = iVar1;
    if (-1 < iVar1) {
      *piVar3 = *piVar3 + *(int *)(*(longlong *)(param_1 + 0x18) + 0x18 + (ulonglong)bVar2 * 4);
    }
    bVar2 = bVar2 + 1;
    piVar3 = piVar3 + 1;
  } while (bVar2 != 2);
  FUN_140e71e30(*(undefined8 *)(param_1 + 0x18),local_10[0],local_10[1]);
  return;
}


