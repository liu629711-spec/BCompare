object DirLegendDialog: TDirLegendDialog
  Caption = 'Legend'
  ClientHeight = 401
  ClientWidth = 401
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  OnHide = FormHide
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object ListBox: TUiListBox
    Left = 8
    Top = 8
    Width = 385
    Height = 354
    TabStop = False
    Anchors = [akLeft, akTop, akRight, akBottom]
    TabOrder = 0
    OnDrawItem = ListBoxDrawItem
    OnHintShowPrep = ListBoxHintShowPrep
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 362
    Width = 401
    TabOrder = 1
    object CloseBtn: TUiCloseBtn
    end
  end
end
