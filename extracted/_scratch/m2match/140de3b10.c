function: FUN_140de3b10
entry: 140de3b10
body_size: 78
signature: undefined FUN_140de3b10()


void FUN_140de3b10(longlong param_1,undefined8 param_2)

{
  longlong lVar1;
  undefined8 uVar2;
  undefined8 local_38;
  undefined8 uStack_30;
  
  uVar2 = FUN_140dc5c60(PTR_LAB_140dc56f0,1,0);
  *(undefined8 *)(param_1 + 0x10) = uVar2;
  FUN_140ddfb90(&local_38,param_2);
  lVar1 = *(longlong *)(param_1 + 0x10);
  *(undefined8 *)(lVar1 + 200) = local_38;
  *(undefined8 *)(lVar1 + 0xd0) = uStack_30;
  return;
}


