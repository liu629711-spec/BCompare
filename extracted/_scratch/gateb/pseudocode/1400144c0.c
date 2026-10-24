function: FUN_1400144c0
entry: 1400144c0
body_size: 135
signature: undefined FUN_1400144c0()


void FUN_1400144c0(longlong *param_1,longlong param_2)

{
  int *piVar1;
  int iVar2;
  longlong lVar3;
  
  if (param_2 != 0) {
    if (*(int *)(param_2 + -8) < 0) {
      iVar2 = *(int *)(param_2 + -4);
      lVar3 = FUN_140013cd0(iVar2);
      FUN_14000a390(param_2,lVar3,(longlong)(iVar2 * 2));
      param_2 = lVar3;
    }
    else {
      LOCK();
      *(int *)(param_2 + -8) = *(int *)(param_2 + -8) + 1;
      UNLOCK();
    }
  }
  lVar3 = *param_1;
  *param_1 = param_2;
  if ((lVar3 != 0) && (0 < *(int *)(lVar3 + -8))) {
    LOCK();
    piVar1 = (int *)(lVar3 + -8);
    iVar2 = *piVar1;
    *piVar1 = *piVar1 + -1;
    UNLOCK();
    if (iVar2 == 1) {
      FUN_140009a30(lVar3 + -0x10);
    }
  }
  return;
}


