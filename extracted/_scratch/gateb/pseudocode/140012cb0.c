function: FUN_140012cb0
entry: 140012cb0
body_size: 313
signature: undefined FUN_140012cb0()


void FUN_140012cb0(longlong param_1,undefined8 param_2,char param_3)

{
  undefined4 local_100;
  undefined4 local_fc;
  undefined8 local_f8;
  undefined8 local_f0;
  undefined4 local_e8;
  undefined8 local_e0;
  longlong local_d8;
  undefined8 local_d0;
  undefined8 local_c8;
  undefined8 local_c0;
  undefined8 local_b8;
  undefined8 local_b0;
  undefined8 local_a8;
  undefined8 local_68;
  longlong local_60;
  undefined8 local_58;
  undefined8 local_50;
  undefined8 local_48;
  undefined8 local_40;
  undefined8 local_38;
  undefined8 local_30;
  
  if (param_1 == 0) {
    FUN_140013ae0(0xd8);
  }
  local_58 = 0;
  local_50 = 0;
  local_48 = 0;
  local_40 = 0;
  local_38 = 0;
  local_30 = 0;
  local_68 = param_2;
  local_60 = param_1;
  if ((DAT_141fb6040 != (code *)0x0) && (param_3 == '\0')) {
    local_100 = 0xeedfade;
    local_fc = 1;
    local_f8 = 0;
    local_e8 = 8;
    local_d0 = 0;
    local_c8 = 0;
    local_c0 = 0;
    local_b8 = 0;
    local_b0 = 0;
    local_a8 = 0;
    local_f0 = param_2;
    local_e0 = param_2;
    local_d8 = param_1;
    (*DAT_141fb6040)(&local_100);
  }
  (*DAT_141fb6030)(0xeedfade,1,8,&local_68);
  return;
}


