function: FUN_140052fe0
entry: 140052fe0
body_size: 98
signature: undefined FUN_140052fe0()


longlong FUN_140052fe0(longlong param_1,char param_2,undefined8 param_3)

{
  undefined1 *puVar1;
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
  FUN_1400144c0(local_res8 + 8,param_3);
  if (param_2 != '\0') {
    local_res8 = FUN_1400112a0(local_res8);
  }
  return local_res8;
}


