function: FUN_140e54d20
entry: 140e54d20
body_size: 212
signature: undefined FUN_140e54d20()


longlong * FUN_140e54d20(longlong *param_1,char param_2)

{
  undefined1 *puVar1;
  longlong lVar2;
  undefined8 uVar3;
  longlong *local_res8;
  undefined1 auStack_48 [40];
  undefined1 *local_20;
  
  local_20 = auStack_48;
  local_res8 = param_1;
  puVar1 = auStack_48;
  if (param_2 != '\0') {
    local_res8 = (longlong *)FUN_140011260(param_1,param_2);
    puVar1 = local_20;
  }
  local_20 = puVar1;
  FUN_14067e8a0(local_res8,0);
  lVar2 = FUN_140131f30(PTR_PTR_140524638,1);
  local_res8[10] = lVar2;
  FUN_140680da0(local_res8,lVar2);
  *(undefined1 *)(local_res8 + 0xf) = 2;
  uVar3 = (**(code **)(*local_res8 + 0x168))(*local_res8);
  lVar2 = FUN_14067e940(uVar3,1,local_res8);
  local_res8[0x11] = lVar2;
  uVar3 = (**(code **)(*local_res8 + 0x170))(*local_res8);
  lVar2 = FUN_14067e940(uVar3,1,local_res8);
  local_res8[0x12] = lVar2;
  if (param_2 != '\0') {
    local_res8 = (longlong *)FUN_1400112a0(local_res8);
  }
  return local_res8;
}


