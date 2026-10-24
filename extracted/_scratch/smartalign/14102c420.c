function: FUN_14102c420
entry: 14102c420
body_size: 72
signature: undefined FUN_14102c420()


undefined8
FUN_14102c420(longlong param_1,undefined8 param_2,ulonglong param_3,undefined4 param_4,
             undefined1 param_5)

{
  undefined8 uVar1;
  
  uVar1 = FUN_141028aa0(*(undefined8 *)(param_1 + 0x10),
                        *(undefined1 *)(param_1 + 8 + (param_3 & 0xff)));
  uVar1 = FUN_141015bf0(uVar1);
  FUN_141012980(uVar1,param_2,param_4,param_5);
  return param_2;
}


