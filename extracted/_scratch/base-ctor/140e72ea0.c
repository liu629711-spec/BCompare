function: FUN_140e72ea0
entry: 140e72ea0
body_size: 133
signature: undefined FUN_140e72ea0()


void FUN_140e72ea0(longlong param_1)

{
  int iVar1;
  
  if (*(int *)(param_1 + 0x98) < 0x1000) {
    for (iVar1 = 2; iVar1 < *(int *)(param_1 + 0x98); iVar1 = iVar1 * 2) {
    }
  }
  else {
    iVar1 = 0x1000;
  }
  *(int *)(param_1 + 0x38) = iVar1 + -1;
  FUN_140019870(param_1 + 0x48,PTR_DAT_140e712f0,1,(longlong)iVar1);
  **(undefined4 **)(param_1 + 0x48) = 0xffffffff;
  FUN_140019870(param_1 + 0x50,PTR_DAT_140e712f0,1,(longlong)iVar1);
  **(undefined4 **)(param_1 + 0x50) = 0xffffffff;
  return;
}


