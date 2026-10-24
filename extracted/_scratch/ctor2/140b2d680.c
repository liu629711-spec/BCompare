function: FUN_140b2d680
entry: 140b2d680
body_size: 344
signature: undefined FUN_140b2d680()


longlong FUN_140b2d680(longlong param_1,char param_2,undefined8 param_3)

{
  undefined1 *puVar1;
  undefined8 uVar2;
  longlong local_res8;
  undefined1 auStack_48 [40];
  undefined1 *local_20;
  
  local_20 = auStack_48;
  local_res8 = param_1;
  puVar1 = auStack_48;
  if (param_2 != '\0') {
    local_res8 = FUN_140011260(param_1,param_2);
    puVar1 = local_20;
  }
  local_20 = puVar1;
  FUN_140b25740(local_res8,0,param_3);
  uVar2 = FUN_140845660(PTR_PTR_1408427f8,1,0);
  *(undefined8 *)(local_res8 + 0xb8) = uVar2;
  *(undefined1 *)(local_res8 + 0xc0) = 1;
  uVar2 = FUN_1400107b0(PTR_PTR_1400e9f60,1);
  *(undefined8 *)(local_res8 + 600) = uVar2;
  uVar2 = FUN_1400107b0(PTR_PTR_1400e9f60,1);
  *(undefined8 *)(local_res8 + 0x260) = uVar2;
  uVar2 = FUN_1400107b0(PTR_PTR_1400e9f60,1);
  *(undefined8 *)(local_res8 + 0x268) = uVar2;
  uVar2 = FUN_1400107b0(PTR_PTR_1400e9f60,1);
  *(undefined8 *)(local_res8 + 0x270) = uVar2;
  uVar2 = FUN_1400107b0(PTR_PTR_1400e9f60,1);
  *(undefined8 *)(local_res8 + 0x278) = uVar2;
  uVar2 = FUN_1400107b0(PTR_PTR_1400e9f60,1);
  *(undefined8 *)(local_res8 + 0x280) = uVar2;
  uVar2 = FUN_1406b2b90();
  *(undefined8 *)(local_res8 + 0x288) = uVar2;
  uVar2 = FUN_1406b2b90();
  *(undefined8 *)(local_res8 + 0x290) = uVar2;
  uVar2 = FUN_1400107b0(PTR_PTR_1400e9f60,1);
  *(undefined8 *)(local_res8 + 0x298) = uVar2;
  if (param_2 != '\0') {
    local_res8 = FUN_1400112a0(local_res8);
  }
  return local_res8;
}


