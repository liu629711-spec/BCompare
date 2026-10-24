function: FUN_141028560
entry: 141028560
body_size: 622
signature: undefined FUN_141028560()


void FUN_141028560(undefined8 param_1,char param_2,undefined4 param_3)

{
  char cVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  undefined8 uVar4;
  longlong *plVar5;
  undefined8 uVar6;
  undefined1 auStack_78 [32];
  undefined1 local_58;
  char local_41;
  longlong local_40 [2];
  undefined4 local_2c;
  
  local_40[0] = 0;
  local_41 = param_2;
  uVar4 = FUN_141028aa0(param_1,param_2);
  uVar4 = FUN_141015bf0(uVar4);
  uVar2 = FUN_141028b00(param_1,param_2,param_3);
  cVar1 = FUN_141011f10(uVar4,uVar2);
  if (cVar1 != '\0') {
    local_2c = FUN_141028b00(param_1,2,param_3);
    plVar5 = (longlong *)FUN_14102a280(param_1);
    cVar1 = (**(code **)(*plVar5 + 0x180))(*plVar5,2);
    if (cVar1 != '\0') {
      uVar4 = FUN_14102a280(param_1);
      FUN_140e686b0(uVar4,local_40,2);
      if (local_40[0] != 0) {
        cVar1 = FUN_141028e40(param_1,2,param_3);
        if (cVar1 == '\0') {
          if (local_41 != '\x02') {
            uVar4 = FUN_141028aa0(param_1,2);
            uVar4 = FUN_141015bf0(uVar4);
            cVar1 = FUN_141011f10(uVar4,local_2c);
            if (cVar1 == '\0') {
              uVar4 = FUN_141028aa0(param_1,2);
              uVar4 = FUN_141015bf0(uVar4);
              uVar4 = FUN_1410117d0(uVar4,local_2c);
              FUN_1410284b0(auStack_78,local_41);
              uVar6 = FUN_141028aa0(param_1,2);
              uVar6 = FUN_141015bf0(uVar6);
              FUN_141011770(uVar6,local_2c,uVar4);
              goto code_r0x0001410287ba;
            }
          }
          FUN_1410284b0(auStack_78,0);
          uVar4 = FUN_141028aa0(param_1,2);
          uVar4 = FUN_141015bf0(uVar4);
          uVar4 = FUN_1410117d0(uVar4,local_2c);
          FUN_1410284b0(auStack_78,1);
          uVar6 = FUN_141028aa0(param_1,2);
          uVar6 = FUN_141015bf0(uVar6);
          FUN_141011450(uVar6,local_2c,uVar4);
          goto code_r0x0001410287ba;
        }
      }
    }
    uVar4 = FUN_141028aa0(param_1,0);
    uVar4 = FUN_141015bf0(uVar4);
    uVar2 = FUN_141028b00(param_1,0,param_3);
    uVar6 = FUN_141028aa0(param_1,1);
    uVar6 = FUN_141015bf0(uVar6);
    uVar3 = FUN_141028b00(param_1,1,param_3);
    local_58 = FUN_141028d90(param_1,param_3);
    FUN_14100f310(uVar4,uVar2,uVar6,uVar3);
  }
code_r0x0001410287ba:
  FUN_140013e30(local_40);
  return;
}


