function: FUN_140e72f30
entry: 140e72f30
body_size: 23
signature: undefined FUN_140e72f30()


undefined1 FUN_140e72f30(longlong param_1,ulonglong param_2,int param_3)

{
  return *(undefined1 *)
          (*(longlong *)(param_1 + 0x70 + (param_2 & 0xff) * 8) +
          (longlong)(param_3 - *(int *)(param_1 + 0x18 + (param_2 & 0xff) * 4)));
}


