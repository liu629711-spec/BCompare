function: FUN_140e73040
entry: 140e73040
body_size: 874
signature: undefined FUN_140e73040()


void FUN_140e73040(longlong param_1,int param_2,int param_3)

{
  int *piVar1;
  undefined4 *puVar2;
  longlong lVar3;
  char cVar4;
  char cVar5;
  int iVar6;
  int iVar7;
  undefined8 uVar8;
  longlong lVar9;
  int iVar10;
  int iVar11;
  
  if (*(char *)(*(longlong *)
                 (*(longlong *)(*(longlong *)(param_1 + 0x90) + 0xa0) +
                 (longlong)(param_2 - *(int *)(*(longlong *)(param_1 + 0x90) + 0x9c)) * 8) +
               (longlong)(param_3 - *(int *)(*(longlong *)(param_1 + 0x90) + 0xa8))) == '\0') {
    *(int *)(param_1 + 0x6c) = param_2;
    *(int *)(param_1 + 0x68) = param_3;
    *(undefined4 *)(param_1 + 100) = 0;
    iVar10 = 0;
    while( true ) {
      iVar6 = FUN_140e72e80(*(undefined8 *)(param_1 + 0x90),0,param_2);
      iVar7 = FUN_140e72e80(*(undefined8 *)(param_1 + 0x90),1,param_3);
      if (iVar6 != iVar7) break;
      cVar4 = FUN_140e72f30(*(undefined8 *)(param_1 + 0x90),0,param_2);
      if (cVar4 == '\0') {
        iVar6 = FUN_140e74a70(*(undefined8 *)(param_1 + 0x90),0,param_2);
      }
      else {
        iVar6 = FUN_140e74a70(*(undefined8 *)(param_1 + 0x90),0,param_2);
      }
      iVar10 = iVar10 + iVar6;
      *(int *)(param_1 + 100) = *(int *)(param_1 + 100) + 1;
      param_2 = param_2 + 1;
      param_3 = param_3 + 1;
      if (4999 < iVar10) {
        uVar8 = FUN_140052fe0(PTR_PTR_140e70a98,1,0);
        FUN_140012e10(uVar8);
      }
      if ((*(char *)(param_1 + 0xb8) == '\0') &&
         ((**(int **)(param_1 + 0xa8) < param_2 || (**(int **)(param_1 + 0xb0) < param_3)))) break;
      cVar4 = FUN_140e722a0(*(undefined8 *)(param_1 + 0x90),0,param_2,
                            *(undefined8 *)(param_1 + 0xa8));
      cVar5 = FUN_140e722a0(*(undefined8 *)(param_1 + 0x90),1,param_3,
                            *(undefined8 *)(param_1 + 0xb0));
      FUN_140ddfb30(*(undefined8 *)(*(longlong *)(param_1 + 0x90) + 8));
      if (cVar4 == '\0' || cVar5 == '\0') break;
    }
    iVar6 = *(int *)(param_1 + 0x6c);
    iVar7 = *(int *)(param_1 + 0x68);
    iVar11 = *(int *)(param_1 + 100) + 1;
    if (0 < iVar11) {
      do {
        *(undefined1 *)
         (*(longlong *)
           (*(longlong *)(*(longlong *)(param_1 + 0x90) + 0xa0) +
           (longlong)(iVar6 - *(int *)(*(longlong *)(param_1 + 0x90) + 0x9c)) * 8) +
         (longlong)(iVar7 - *(int *)(*(longlong *)(param_1 + 0x90) + 0xa8))) = 1;
        iVar6 = iVar6 + 1;
        iVar7 = iVar7 + 1;
        if ((**(int **)(param_1 + 0xa8) < iVar6) || (**(int **)(param_1 + 0xb0) < iVar7)) break;
        FUN_140e72330(*(undefined8 *)(param_1 + 0x90),
                      iVar6 - *(int *)(*(longlong *)(param_1 + 0x90) + 0x9c));
        iVar11 = iVar11 + -1;
      } while (iVar11 != 0);
    }
    if (500 < iVar10) {
      lVar3 = *(longlong *)(*(longlong *)(param_1 + 0x90) + 0x90);
      lVar9 = 0;
      if (lVar3 != 0) {
        lVar9 = *(longlong *)(lVar3 + -8);
      }
      iVar6 = *(int *)(*(longlong *)(param_1 + 0x90) + 0x88);
      if (iVar6 == lVar9) {
        iVar6 = FUN_14052a190(iVar6,0x80);
        FUN_140019870(*(longlong *)(param_1 + 0x90) + 0x90,PTR_DAT_140e713e8,1,(longlong)iVar6);
      }
      puVar2 = (undefined4 *)
               (*(longlong *)(*(longlong *)(param_1 + 0x90) + 0x90) +
               (longlong)*(int *)(*(longlong *)(param_1 + 0x90) + 0x88) * 0x10);
      *puVar2 = *(undefined4 *)(param_1 + 100);
      puVar2[1] = iVar10;
      puVar2[2] = *(undefined4 *)(param_1 + 0x6c);
      puVar2[3] = *(undefined4 *)(param_1 + 0x68);
      piVar1 = (int *)(*(longlong *)(param_1 + 0x90) + 0x88);
      *piVar1 = *piVar1 + 1;
    }
  }
  return;
}


