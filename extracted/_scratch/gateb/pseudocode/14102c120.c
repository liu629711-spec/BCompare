function: FUN_14102c120
entry: 14102c120
body_size: 98
signature: undefined FUN_14102c120()


void FUN_14102c120(longlong param_1,uint param_2,undefined4 *param_3,undefined4 *param_4)

{
  ulonglong uVar1;
  
  FUN_14102b4c0(param_1,(ulonglong)param_2,param_3,param_4);
  *param_3 = *(undefined4 *)(param_1 + 0x160);
  uVar1 = (ulonglong)param_2 & 0xff;
  *(undefined4 *)(param_1 + 0x138 + uVar1 * 4) = *(undefined4 *)(param_1 + 0x158 + uVar1 * 4);
  *param_4 = *(undefined4 *)(param_1 + 0x16c);
  *(undefined4 *)(param_1 + 0x140 + uVar1 * 4) = *(undefined4 *)(param_1 + 0x164 + uVar1 * 4);
  return;
}


