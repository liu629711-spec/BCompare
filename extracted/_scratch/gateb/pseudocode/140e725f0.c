function: FUN_140e725f0
entry: 140e725f0
body_size: 185
signature: undefined FUN_140e725f0()


int FUN_140e725f0(undefined8 param_1,longlong param_2,longlong param_3)

{
  byte bVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  short local_218 [256];
  
  FUN_14000dce0(local_218,0x200,0);
  iVar2 = 0;
  if (param_2 != 0) {
    iVar2 = *(int *)(param_2 + -4);
  }
  iVar3 = 1;
  if (0 < iVar2) {
    do {
      local_218[*(byte *)(param_2 + -1 + (longlong)iVar3)] =
           local_218[*(byte *)(param_2 + -1 + (longlong)iVar3)] + 1;
      iVar3 = iVar3 + 1;
      iVar2 = iVar2 + -1;
    } while (iVar2 != 0);
  }
  iVar3 = 0;
  iVar2 = 0;
  if (param_3 != 0) {
    iVar2 = *(int *)(param_3 + -4);
  }
  iVar4 = 1;
  if (0 < iVar2) {
    do {
      bVar1 = *(byte *)(param_3 + -1 + (longlong)iVar4);
      local_218[bVar1] = local_218[bVar1] + -1;
      if (-1 < local_218[bVar1]) {
        iVar3 = iVar3 + 1;
      }
      iVar4 = iVar4 + 1;
      iVar2 = iVar2 + -1;
    } while (iVar2 != 0);
  }
  return iVar3;
}


