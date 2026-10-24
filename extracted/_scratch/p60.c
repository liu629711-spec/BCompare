function: FUN_1410347f0
entry: 1410347f0
body_size: 206
signature: undefined FUN_1410347f0()


longlong * FUN_1410347f0(longlong *param_1,char param_2)

{
  undefined1 *puVar1;
  char cVar2;
  longlong lVar3;
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
  FUN_140e63570(local_res8,0);
  lVar3 = FUN_141022630(PTR_DAT_14101e428,1,local_res8);
  local_res8[0x52] = lVar3;
  FUN_141035a70(local_res8);
  lVar3 = FUN_14102dca0(PTR_DAT_14102cf50,1,local_res8);
  local_res8[0x51] = lVar3;
  cVar2 = (**(code **)(*local_res8 + 0x180))(*local_res8,3);
  if (cVar2 != '\0') {
    lVar3 = FUN_141018aa0(PTR_DAT_141016ab8,1,local_res8);
    local_res8[0x54] = lVar3;
  }
  if (param_2 != '\0') {
    local_res8 = (longlong *)FUN_1400112a0(local_res8);
  }
  return local_res8;
}


