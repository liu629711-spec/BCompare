function: FUN_1410273b0
entry: 1410273b0
body_size: 784
signature: undefined FUN_1410273b0()


void FUN_1410273b0(undefined8 param_1,longlong param_2)

{
  byte bVar1;
  uint uVar2;
  int iVar3;
  undefined4 uVar4;
  undefined8 uVar5;
  longlong lVar6;
  longlong lVar7;
  ulonglong uVar8;
  undefined8 uVar9;
  ulonglong uVar10;
  ulonglong uVar11;
  byte bVar12;
  byte bVar13;
  uint *puVar14;
  bool bVar15;
  uint local_40 [4];
  
  uVar5 = FUN_141028aa0(param_1,0);
  uVar5 = FUN_141015bf0(uVar5);
  lVar6 = FUN_1406732e0(uVar5);
  uVar5 = FUN_141028aa0(param_1,1);
  uVar5 = FUN_141015bf0(uVar5);
  lVar7 = FUN_1406732e0(uVar5);
  *(longlong *)(param_2 + 0x70) = lVar6 + lVar7;
  local_40[0] = 0;
  local_40[1] = 0;
  uVar11 = 1;
  while( true ) {
    FUN_140ddfb30(param_2);
    uVar5 = FUN_141028aa0(param_1,0);
    uVar5 = FUN_141015bf0(uVar5);
    lVar6 = FUN_1406732c0(uVar5);
    uVar5 = FUN_141028aa0(param_1,1);
    uVar5 = FUN_141015bf0(uVar5);
    lVar7 = FUN_1406732c0(uVar5);
    *(longlong *)(param_2 + 0x68) = lVar6 + lVar7;
    bVar12 = 0;
    puVar14 = local_40;
    bVar13 = DAT_1410276c0;
    do {
      uVar5 = FUN_141028aa0(param_1,bVar12);
      uVar5 = FUN_141015bf0(uVar5);
      uVar10 = (ulonglong)*puVar14;
      uVar8 = FUN_140670ec0(uVar5,uVar10);
      if (((char)uVar8 != '\0') && (bVar12 < 8)) {
        uVar2 = (int)CONCAT71((int7)(uVar8 >> 8),1) << (bVar12 & 0x1f);
        uVar8 = (ulonglong)uVar2;
        bVar13 = bVar13 | (byte)uVar2;
      }
      bVar12 = bVar12 + 1;
      puVar14 = puVar14 + 1;
    } while (bVar12 != 2);
    if (bVar13 == DAT_1410276c0) break;
    if (bVar13 == DAT_1410276c1) {
      uVar5 = FUN_141029730(param_1);
      uVar10 = 0;
      uVar8 = FUN_140682190(uVar5,2);
      if ((char)uVar8 == '\0') {
        bVar12 = 0;
        puVar14 = local_40;
        do {
          uVar5 = FUN_141028aa0(param_1,bVar12);
          uVar5 = FUN_141015bf0(uVar5);
          uVar10 = (ulonglong)*puVar14;
          uVar8 = FUN_141011db0(uVar5,uVar10);
          if (((char)uVar8 != '\0') && (bVar12 < 8)) {
            iVar3 = (int)CONCAT71((int7)(uVar8 >> 8),1) << (bVar12 & 0x1f);
            bVar1 = ~(byte)iVar3;
            uVar8 = (ulonglong)CONCAT31((int3)((uint)iVar3 >> 8),bVar1);
            bVar13 = bVar13 & bVar1;
          }
          bVar12 = bVar12 + 1;
          puVar14 = puVar14 + 1;
        } while (bVar12 != 2);
        if (bVar13 == DAT_1410276c0) {
          bVar13 = DAT_1410276c1;
        }
      }
    }
    uVar5 = CONCAT71((int7)(uVar8 >> 8),1);
    if (bVar13 == DAT_1410276c1) {
      uVar5 = FUN_141028aa0(param_1,0);
      uVar5 = FUN_141015bf0(uVar5);
      uVar9 = FUN_141028aa0(param_1,1);
      uVar9 = FUN_141015bf0(uVar9);
      uVar4 = FUN_14100fba0(uVar5,local_40[0],uVar9,local_40[1]);
    }
    else {
      bVar12 = 0;
      puVar14 = local_40;
      do {
        if (bVar12 < 8) {
          uVar2 = (int)CONCAT71((int7)(uVar10 >> 8),1) << (bVar12 & 0x1f);
          uVar10 = (ulonglong)uVar2;
          bVar15 = ((byte)uVar2 & bVar13) != 0;
        }
        else {
          bVar15 = false;
        }
        if (bVar15) {
          uVar5 = FUN_141028aa0(param_1,bVar12);
          uVar5 = FUN_141015bf0(uVar5);
          uVar10 = (ulonglong)*puVar14;
          uVar5 = FUN_141010900(uVar5,uVar10);
        }
        uVar4 = (undefined4)uVar5;
        bVar12 = bVar12 + 1;
        puVar14 = puVar14 + 1;
      } while (bVar12 != 2);
    }
    uVar10 = FUN_140e6b9b0(uVar4);
    uVar11 = uVar10 & 0xffffffff;
    if ((char)uVar11 == '\x04') break;
    bVar12 = 0;
    puVar14 = local_40;
    do {
      if (bVar12 < 8) {
        iVar3 = (int)CONCAT71((int7)(uVar10 >> 8),1) << (bVar12 & 0x1f);
        uVar10 = (ulonglong)CONCAT31((int3)((uint)iVar3 >> 8),((byte)iVar3 & bVar13) != 0);
      }
      else {
        uVar10 = 0;
      }
      if ((char)uVar10 != '\0') {
        do {
          *puVar14 = *puVar14 + 1;
          if ((char)uVar11 == '\x01') break;
          uVar5 = FUN_141029730(param_1);
          uVar10 = FUN_140682190(uVar5);
          if ((char)uVar10 != '\0') break;
          uVar5 = FUN_141028aa0(param_1,bVar12);
          uVar5 = FUN_141015bf0(uVar5);
          uVar10 = FUN_140670ec0(uVar5);
          if ((char)uVar10 == '\0') break;
          uVar5 = FUN_141028aa0(param_1,bVar12);
          uVar5 = FUN_141015bf0(uVar5);
          uVar10 = FUN_141011db0(uVar5);
        } while ((char)uVar10 == '\0');
      }
      bVar12 = bVar12 + 1;
      puVar14 = puVar14 + 1;
    } while (bVar12 != 2);
  }
  uVar5 = FUN_14102a280(param_1);
  FUN_140e66fc0(uVar5,PTR_DAT_141faf708[uVar11 & 0xff]);
  return;
}


