function: FUN_140ad3ba0
entry: 140ad3ba0
body_size: 150
signature: undefined FUN_140ad3ba0()


undefined8 FUN_140ad3ba0(longlong param_1,int param_2)

{
  int iVar1;
  undefined8 uVar2;
  undefined8 local_18;
  undefined8 local_10;
  
  local_10 = 0;
  if (-1 < param_2) {
    iVar1 = FUN_140ad3b90(param_1);
    if (param_2 < iVar1) {
      local_18 = FUN_140129dc0(*(undefined8 *)(param_1 + 8),(longlong)param_2);
      goto code_r0x000140ad3c23;
    }
  }
  FUN_14001e690(&local_10,PTR_LAB_141fb3398);
  uVar2 = FUN_1406e4310(PTR_PTR_1409d7a70,1,0xb1003,local_10,param_2);
  FUN_140012e10(uVar2);
code_r0x000140ad3c23:
  FUN_140013e30(&local_10);
  return local_18;
}


