function: FUN_140b5ed30
entry: 140b5ed30
body_size: 2479
signature: undefined FUN_140b5ed30()


void FUN_140b5ed30(longlong param_1,longlong param_2,char param_3)

{
  int iVar1;
  int iVar2;
  undefined8 uVar3;
  longlong lVar4;
  undefined1 auStack_178 [32];
  undefined *local_158;
  wchar_t *local_150;
  undefined8 local_140;
  undefined8 local_138;
  undefined8 local_130;
  undefined8 local_128;
  undefined8 local_120;
  undefined8 local_118;
  undefined8 local_110;
  undefined8 local_108;
  undefined8 local_100;
  undefined8 local_f8;
  undefined8 local_f0;
  longlong local_e8;
  undefined8 local_e0;
  longlong local_d8;
  undefined8 local_d0;
  undefined8 local_c8;
  undefined8 local_c0;
  undefined8 local_b8;
  undefined8 local_b0;
  undefined8 local_a8;
  undefined8 local_a0;
  undefined8 local_98;
  undefined8 local_90;
  undefined8 local_88;
  undefined1 *local_80;
  int local_74;
  longlong local_70;
  int local_64;
  longlong local_60;
  int local_54;
  longlong local_50;
  int local_40;
  int local_3c;
  longlong *local_38;
  longlong local_30;
  longlong local_28;
  longlong *local_20;
  
  local_80 = auStack_178;
  local_138 = 0;
  local_130 = 0;
  local_128 = 0;
  local_120 = 0;
  local_110 = 0;
  local_118 = 0;
  local_108 = 0;
  local_100 = 0;
  local_f0 = 0;
  local_f8 = 0;
  local_e8 = 0;
  local_e0 = 0;
  local_d8 = 0;
  local_c8 = 0;
  local_d0 = 0;
  local_c0 = 0;
  local_b8 = 0;
  local_b0 = 0;
  local_a8 = 0;
  local_a0 = 0;
  local_98 = 0;
  local_90 = 0;
  local_88 = 0;
  FUN_140b5dc00(param_1);
  if (param_2 == 0) {
    FUN_14001e690(&local_88,PTR_LAB_141fb5470);
    uVar3 = FUN_1406e4070(PTR_PTR_140b49620,1,0xb510c,local_88);
    FUN_140012e10(uVar3);
  }
  if (param_3 == '\0') {
    *(longlong *)(param_1 + 0xb8) = param_2;
    *(undefined1 *)(param_1 + 0xd8) = 0;
  }
  else {
    uVar3 = FUN_140a128a0(param_2);
    *(undefined8 *)(param_1 + 0xb8) = uVar3;
    *(undefined1 *)(param_1 + 0xd8) = 1;
  }
  local_20 = (longlong *)FUN_140a11e70(*(undefined8 *)(param_1 + 0xb8));
  (**(code **)(*local_20 + 8))(local_20,&local_90);
  iVar1 = FUN_140016350(local_90,L"TrustServiceStatusList");
  if (iVar1 != 0) {
    FUN_14001e690(&local_98,PTR_LAB_141fae008);
    local_158 = &DAT_140b5f774;
    local_150 = L"TrustServiceStatusList";
    uVar3 = FUN_1406e46c0(PTR_PTR_140b49620,1,0xb510d,local_98);
    FUN_140012e10(uVar3);
  }
  (**(code **)(*local_20 + 0x20))(local_20,&local_a0);
  iVar1 = FUN_140016350(local_a0,L"http://uri.etsi.org/02231/v2#");
  if (iVar1 == 0) {
    *(undefined1 *)(param_1 + 0xa0) = 4;
  }
  else {
    (**(code **)(*local_20 + 0x20))(local_20,&local_a8);
    iVar1 = FUN_140016350(local_a8,L"http://uri.etsi.org/02231/v1.1.1#");
    if (iVar1 == 0) {
      *(undefined1 *)(param_1 + 0xa0) = 0;
    }
    else {
      uVar3 = FUN_1406e3fc0(PTR_PTR_140b494e8,1,L"Invalid TrustedList namespace URI");
      FUN_140012e10(uVar3);
    }
  }
  FUN_140a05fa0(local_20,&local_b0,L"TSLTag");
  FUN_1400144c0(param_1 + 0x98,local_b0);
  if (*(char *)(param_1 + 0xa0) == '\x04') {
    iVar1 = FUN_140016350(*(undefined8 *)(param_1 + 0x98),L"http://uri.etsi.org/02231/TSLTag");
    if (iVar1 == 0) {
      *(undefined1 *)(param_1 + 0xa0) = 3;
    }
    else {
      iVar1 = FUN_140016350(*(undefined8 *)(param_1 + 0x98),L"http://uri.etsi.org/19612/TSLTag");
      if (iVar1 != 0) {
        uVar3 = FUN_1406e3fc0(PTR_PTR_140b494e8,1,L"Invalid TSLTag value");
        FUN_140012e10(uVar3);
      }
    }
    FUN_140a05fa0(local_20,&local_b8,&DAT_140b5f964);
    FUN_1400144c0(param_1 + 0x90,local_b8);
  }
  FUN_140013e30(param_1 + 200);
  lVar4 = (**(code **)(*local_20 + 0x88))();
  iVar1 = *(int *)(lVar4 + 0x10);
  local_40 = 0;
  if (-1 < iVar1 + -1) {
    do {
      uVar3 = (**(code **)(*local_20 + 0x88))(local_20);
      local_38 = (longlong *)FUN_140a04270(uVar3,local_40);
      (**(code **)(*local_38 + 0x18))(local_38,&local_c0);
      iVar2 = FUN_140016350(local_c0,L"xmlns");
      if (iVar2 == 0) {
        (**(code **)(*local_20 + 0x20))(local_20,&local_c8);
        (**(code **)(*local_38 + 0x78))(local_38,&local_d0);
        iVar2 = FUN_140016350(local_c8,local_d0);
        if (iVar2 == 0) {
          local_50 = *(longlong *)(param_1 + 200);
          local_54 = 0;
          if (local_50 != 0) {
            local_54 = *(int *)(local_50 + -4);
          }
          if (0 < local_54) {
            FUN_140016090(param_1 + 200,&DAT_140b5f990);
          }
          (**(code **)(*local_38 + 8))(local_38,&local_d8);
          local_60 = local_d8;
          local_64 = 0;
          if (local_d8 != 0) {
            local_64 = *(int *)(local_d8 + -4);
          }
          if (local_64 < 1) {
            FUN_140016090(param_1 + 200,L"#default");
          }
          else {
            (**(code **)(*local_38 + 8))(local_38,&local_e0);
            FUN_140016090(param_1 + 200,local_e0);
          }
        }
        else {
          (**(code **)(*local_38 + 8))(local_38,&local_e8);
          local_70 = local_e8;
          local_74 = 0;
          if (local_e8 != 0) {
            local_74 = *(int *)(local_e8 + -4);
          }
          if (0 < local_74) {
            (**(code **)(*local_38 + 8))(local_38,&local_f0);
            (**(code **)(*local_38 + 0x78))(local_38,&local_f8);
            FUN_140a14880(*(undefined8 *)(param_1 + 0xd0),local_f0,local_f8);
          }
        }
      }
      local_40 = local_40 + 1;
      iVar1 = iVar1 + -1;
    } while (iVar1 != 0);
  }
  (**(code **)(*local_20 + 0x20))(local_20,&local_100);
  local_28 = FUN_1409e3ac0(local_20,L"SchemeInformation",local_100);
  if (local_28 == 0) {
    uVar3 = FUN_1406e3fc0(PTR_PTR_140b494e8,1,
                          L"XML element not found (tsl:SchemeInformation element)");
    FUN_140012e10(uVar3);
  }
  FUN_140b498b0(&local_108,*(undefined1 *)(param_1 + 0xa0));
  local_30 = FUN_1409e3ac0(local_28,L"TSLVersionIdentifier",local_108);
  if (local_30 == 0) {
    uVar3 = FUN_1406e3fc0(PTR_PTR_140b494e8,1,
                          L"XML element not found (tsl:TSLVersionIdentifier element)");
    FUN_140012e10(uVar3);
  }
  FUN_1409e3360(&local_118,local_30);
  FUN_1409e4be0(&local_110,local_118);
  local_3c = FUN_140044f00(local_110,0);
  if ((*(char *)(param_1 + 0xa0) == '\0') && (local_3c != 1)) {
    FUN_14001e690(&local_120,&LAB_140b5d480);
    uVar3 = FUN_1406e3fc0(PTR_PTR_140b494e8,1,local_120);
    FUN_140012e10(uVar3);
  }
  if (*(char *)(param_1 + 0xa0) == '\x04') {
    if (local_3c == 4) {
      *(undefined1 *)(param_1 + 0xa0) = 3;
    }
    else if (local_3c != 5) {
      FUN_14001e690(&local_128,&LAB_140b5d480);
      uVar3 = FUN_1406e3fc0(PTR_PTR_140b494e8,1,local_128);
      FUN_140012e10(uVar3);
    }
  }
  else if (*(char *)(param_1 + 0xa0) == '\x03') {
    if (local_3c == 2) {
      *(undefined1 *)(param_1 + 0xa0) = 1;
    }
    else if (local_3c == 3) {
      *(undefined1 *)(param_1 + 0xa0) = 2;
    }
    else if (local_3c == 5) {
      *(undefined1 *)(param_1 + 0xa0) = 4;
    }
    else if (local_3c != 4) {
      FUN_14001e690(&local_130,&LAB_140b5d480);
      uVar3 = FUN_1406e3fc0(PTR_PTR_140b494e8,1,local_130);
      FUN_140012e10(uVar3);
    }
  }
  (**(code **)(**(longlong **)(param_1 + 0x80) + 0x30))
            (*(longlong **)(param_1 + 0x80),local_28,*(undefined1 *)(param_1 + 0xa0));
  (**(code **)(*local_20 + 0x20))(local_20,&local_138);
  local_28 = FUN_1409e3ac0(local_20,L"TrustServiceProviderList",local_138);
  if (local_28 != 0) {
    (**(code **)(**(longlong **)(param_1 + 0x88) + 8))(*(longlong **)(param_1 + 0x88),local_28);
  }
  local_28 = FUN_1409e3ac0(local_20,L"Signature",L"http://www.w3.org/2000/09/xmldsig#");
  if (local_28 != 0) {
    local_140 = FUN_140b5fe30(PTR_DAT_140b5b2b0,1);
    *(undefined8 *)(param_1 + 0xc0) = local_140;
    FUN_140b611e0(local_140,local_28,param_1);
  }
  FUN_140013f10(&local_138,0x17);
  return;
}


