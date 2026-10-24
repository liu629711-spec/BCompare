function: FUN_140e74080
entry: 140e74080
body_size: 113
signature: undefined FUN_140e74080()


void FUN_140e74080(longlong param_1,int *param_2)

{
  int iVar1;
  int iVar2;
  int iVar3;
  
  param_2[1] = 0;
  iVar3 = *param_2;
  iVar2 = 0;
  if (-1 < iVar3 + -1) {
    do {
      iVar1 = FUN_140e74a70(*(undefined8 *)(param_1 + 0x90),0,param_2[2] + iVar2);
      param_2[1] = param_2[1] + iVar1;
      iVar2 = iVar2 + 1;
      iVar3 = iVar3 + -1;
    } while (iVar3 != 0);
  }
  if (param_2[1] < 500) {
    param_2[1] = 0;
  }
  return;
}


