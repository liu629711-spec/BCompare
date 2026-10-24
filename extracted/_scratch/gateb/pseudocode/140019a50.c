function: FUN_140019a50
entry: 140019a50
body_size: 149
signature: undefined FUN_140019a50()


longlong * FUN_140019a50(longlong *param_1,longlong param_2)

{
  int *piVar1;
  int iVar2;
  longlong lVar3;
  undefined8 *puVar4;
  
  lVar3 = *param_1;
  if (lVar3 != 0) {
    *param_1 = 0;
    if (0 < *(int *)(lVar3 + -0xc)) {
      LOCK();
      piVar1 = (int *)(lVar3 + -0xc);
      iVar2 = *piVar1;
      *piVar1 = *piVar1 + -1;
      UNLOCK();
      if (iVar2 == 1) {
        puVar4 = *(undefined8 **)(param_2 + (ulonglong)*(byte *)(param_2 + 1) + 6);
        if ((puVar4 != (undefined8 *)0x0) && (*(longlong *)(lVar3 + -8) != 0)) {
          FUN_140017970(lVar3,*puVar4,*(longlong *)(lVar3 + -8));
        }
        FUN_140009a30(lVar3 + -0x10);
      }
    }
  }
  return param_1;
}


