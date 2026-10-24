function: FUN_14102c490
entry: 14102c490
body_size: 73
signature: undefined FUN_14102c490()


undefined8 FUN_14102c490(longlong param_1,undefined8 param_2,ulonglong param_3,undefined4 param_4)

{
  undefined8 uVar1;
  undefined8 *puVar2;
  
  uVar1 = FUN_141028aa0(*(undefined8 *)(param_1 + 0x10),
                        *(undefined1 *)(param_1 + 8 + (param_3 & 0xff)));
  uVar1 = FUN_141015bf0(uVar1);
  puVar2 = (undefined8 *)FUN_140672d20(uVar1,param_4);
  FUN_1400144c0(param_2,*puVar2);
  return param_2;
}


