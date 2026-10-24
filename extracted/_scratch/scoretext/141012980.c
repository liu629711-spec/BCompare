function: FUN_141012980
entry: 141012980
body_size: 371
signature: undefined FUN_141012980()


undefined8 FUN_141012980(undefined8 param_1,undefined8 param_2,int param_3,char param_4)

{
  undefined8 *puVar1;
  undefined8 uVar2;
  undefined2 uVar3;
  longlong lVar4;
  ulonglong uVar5;
  int iVar6;
  ulonglong uVar7;
  bool bVar8;
  longlong local_58;
  longlong local_50;
  undefined8 local_48;
  undefined8 uStack_40;
  undefined8 uStack_38;
  longlong local_30;
  
  local_30 = 0;
  local_50 = 0;
  local_58 = 0;
  if (param_3 < 0) {
    FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Text\\TextContent.pas",0x909
                 );
  }
  FUN_14100d850(param_1,&local_50,param_3,0);
  uVar7 = 0;
  if (local_50 != 0) {
    uVar7 = *(ulonglong *)(local_50 + -8);
  }
  FUN_140015fb0(&local_30,uVar7 & 0xffffffff);
  iVar6 = 0;
  FUN_140019af0(&local_58,local_50,PTR_DAT_1410097a0);
  uVar7 = 0;
  while( true ) {
    uVar5 = 0;
    if (local_58 != 0) {
      uVar5 = *(ulonglong *)(local_58 + -8);
    }
    if (uVar5 <= uVar7) break;
    puVar1 = (undefined8 *)(local_58 + uVar7 * 0x18);
    local_48 = *puVar1;
    uVar2 = puVar1[1];
    uStack_38 = puVar1[2];
    uStack_40._5_1_ = (char)((ulonglong)uVar2 >> 0x28);
    bVar8 = uStack_40._5_1_ != '\0';
    uStack_40 = uVar2;
    if (bVar8) {
      iVar6 = iVar6 + 1;
      lVar4 = FUN_140014830(&local_30);
      *(undefined2 *)(lVar4 + -2 + (longlong)iVar6 * 2) = uStack_38._4_2_;
      if ((param_4 == '\0') && ((char)local_48 == '\0')) {
        uVar3 = FUN_140525810(*(undefined2 *)(local_30 + -2 + (longlong)iVar6 * 2));
        lVar4 = FUN_140014830(&local_30);
        *(undefined2 *)(lVar4 + -2 + (longlong)iVar6 * 2) = uVar3;
      }
    }
    uVar7 = uVar7 + 1;
  }
  FUN_140019a50(&local_58,PTR_DAT_1410097a0);
  FUN_140015fb0(&local_30,iVar6);
  FUN_1400144c0(param_2,local_30);
  FUN_140017970(&local_58,PTR_DAT_1410097a0,2);
  FUN_140013e30(&local_30);
  return param_2;
}


