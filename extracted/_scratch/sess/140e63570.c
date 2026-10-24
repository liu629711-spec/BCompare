function: FUN_140e63570
entry: 140e63570
body_size: 391
signature: undefined FUN_140e63570()


longlong * FUN_140e63570(longlong *param_1,char param_2)

{
  undefined1 *puVar1;
  char cVar2;
  longlong lVar3;
  longlong *local_res8;
  undefined1 auStack_58 [40];
  undefined1 *local_30;
  byte local_19;
  
  local_30 = auStack_58;
  local_res8 = param_1;
  puVar1 = auStack_58;
  if (param_2 != '\0') {
    local_res8 = (longlong *)FUN_140011260(param_1,param_2);
    puVar1 = local_30;
  }
  local_30 = puVar1;
  FUN_140e54d20(local_res8,0);
  lVar3 = FUN_14008c1d0(PTR_LAB_14008ae70,1);
  local_res8[0x25] = lVar3;
  lVar3 = FUN_1400107b0(PTR_DAT_1405f0aa0,1);
  local_res8[0x28] = lVar3;
  *(longlong **)(lVar3 + 0x48) = local_res8;
  *(code **)(lVar3 + 0x40) = FUN_140e64790;
  *(longlong **)(lVar3 + 0x58) = local_res8;
  *(code **)(lVar3 + 0x50) = FUN_140e64890;
  *(longlong **)(lVar3 + 0x68) = local_res8;
  *(code **)(lVar3 + 0x60) = FUN_140e648b0;
  *(longlong **)(lVar3 + 0x78) = local_res8;
  *(code **)(lVar3 + 0x70) = FUN_140e648d0;
  local_19 = 0;
  do {
    cVar2 = (**(code **)(*local_res8 + 0x180))(*local_res8,local_19);
    if (cVar2 != '\0') {
      lVar3 = (**(code **)(*local_res8 + 0x260))(*local_res8);
      lVar3 = (**(code **)(lVar3 + 0xa0))(lVar3,1,local_res8);
      local_res8[(ulonglong)local_19 + 0x21] = lVar3;
    }
    local_19 = local_19 + 1;
  } while (local_19 != 3);
  cVar2 = (**(code **)(*local_res8 + 0x180))(*local_res8,3);
  if (cVar2 != '\0') {
    *(undefined4 *)(local_res8 + 0x29) = 0x65;
    lVar3 = (**(code **)(*local_res8 + 0x278))(*local_res8);
    lVar3 = (**(code **)(lVar3 + 0xa0))(lVar3,1,local_res8);
    local_res8[0x24] = lVar3;
  }
  *(undefined1 *)(local_res8 + 0x4b) = 6;
  if (param_2 != '\0') {
    local_res8 = (longlong *)FUN_1400112a0(local_res8);
  }
  return local_res8;
}


