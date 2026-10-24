function: FUN_140de3c60
entry: 140de3c60
body_size: 117
signature: undefined FUN_140de3c60()


void FUN_140de3c60(undefined8 param_1,undefined8 param_2,longlong *param_3)

{
  int iVar1;
  int *piVar2;
  longlong *plVar3;
  int iVar4;
  longlong local_20 [2];
  int local_10 [2];
  
  iVar4 = 2;
  piVar2 = local_10;
  plVar3 = local_20;
  do {
    iVar1 = 0;
    if (*param_3 != 0) {
      iVar1 = (int)*(undefined8 *)(*param_3 + -8);
    }
    *piVar2 = iVar1;
    if (iVar1 == 0) {
      *plVar3 = 0;
    }
    else {
      *plVar3 = *param_3;
    }
    plVar3 = plVar3 + 1;
    piVar2 = piVar2 + 1;
    param_3 = param_3 + 1;
    iVar4 = iVar4 + -1;
  } while (iVar4 != 0);
  FUN_140de3420(param_1,param_2,local_20,1,local_10,1);
  return;
}


