function: FUN_14102a380
entry: 14102a380
body_size: 313
signature: undefined FUN_14102a380()


void FUN_14102a380(longlong param_1,undefined8 param_2,int param_3,int param_4,int param_5)

{
  undefined8 uVar1;
  int iVar2;
  undefined1 auStack_48 [40];
  undefined1 *local_20;
  int local_10;
  int local_c;
  
  local_20 = auStack_48;
  uVar1 = FUN_14102a280(*(undefined8 *)(param_1 + 0xe8));
  FUN_140e64df0(uVar1);
  local_10 = *(int *)(*(longlong *)(param_1 + 0xe8) + 0x30);
  FUN_141025c40(*(longlong *)(param_1 + 0xe8),local_10,param_5);
  local_c = 0;
  iVar2 = param_5;
  if (-1 < param_5 + -1) {
    do {
      if (-1 < param_3) {
        *(int *)(*(longlong *)(*(longlong *)(param_1 + 0xe8) + 0x48) +
                (longlong)(local_10 + local_c) * 0x14) = param_3 + local_c;
      }
      if (-1 < param_4) {
        *(int *)(*(longlong *)(*(longlong *)(param_1 + 0xe8) + 0x48) + 4 +
                (longlong)(local_10 + local_c) * 0x14) = param_4 + local_c;
      }
      local_c = local_c + 1;
      iVar2 = iVar2 + -1;
    } while (iVar2 != 0);
  }
  FUN_141027b90(*(undefined8 *)(param_1 + 0xe8),local_10,local_10 + param_5 + -1);
  FUN_1410227d0(*(undefined8 *)(param_1 + 0xe8),local_10);
  FUN_141027e40(*(undefined8 *)(param_1 + 0xe8),local_10);
  uVar1 = FUN_14102a280(*(undefined8 *)(param_1 + 0xe8));
  FUN_140e66a40(uVar1);
  return;
}


