function: FUN_140e72e80
entry: 140e72e80
body_size: 22
signature: undefined FUN_140e72e80()


undefined4 FUN_140e72e80(longlong param_1,ulonglong param_2,int param_3)

{
  return *(undefined4 *)
          (*(longlong *)(param_1 + 0x60 + (param_2 & 0xff) * 8) +
          (longlong)(param_3 - *(int *)(param_1 + 0x18 + (param_2 & 0xff) * 4)) * 4);
}


