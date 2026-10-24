function: FUN_141029ee0
entry: 141029ee0
body_size: 94
signature: undefined FUN_141029ee0()


undefined8
FUN_141029ee0(undefined8 param_1,undefined8 param_2,undefined4 param_3,undefined4 param_4)

{
  int iVar1;
  undefined8 uVar2;
  
  iVar1 = FUN_141028b00(param_1,param_3,param_4);
  if (iVar1 < 0) {
    FUN_140013e30(param_2);
  }
  else {
    uVar2 = FUN_141028aa0(param_1,param_3);
    uVar2 = FUN_141015bf0(uVar2);
    FUN_141012bd0(uVar2,param_2,iVar1);
  }
  return param_2;
}


