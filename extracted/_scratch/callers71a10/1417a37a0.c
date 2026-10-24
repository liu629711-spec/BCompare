function: FUN_1417a37a0
entry: 1417a37a0
body_size: 139
signature: undefined FUN_1417a37a0()


void FUN_1417a37a0(longlong param_1,int param_2,int param_3)

{
  int iVar1;
  
  FUN_1417a0710(*(undefined8 *)(param_1 + 0xe8),*(undefined4 *)(param_1 + 0xf0),param_2,
                param_2 + param_3 + -1);
  if (*(longlong *)(param_1 + 0x150) != 0) {
    iVar1 = FUN_1417a2270(*(undefined8 *)(param_1 + 0xe8),*(undefined4 *)(param_1 + 0xf0));
    if (0x31 < iVar1) {
      iVar1 = 0x32;
    }
    if (param_2 < iVar1) {
      FUN_1417b4d90(*(undefined8 *)(param_1 + 0x150),param_2,iVar1 + -1);
      FUN_1417a0f70(*(undefined8 *)(param_1 + 0xe8),*(undefined4 *)(param_1 + 0xf0),
                    *(undefined8 *)(param_1 + 0x150));
    }
  }
  return;
}


