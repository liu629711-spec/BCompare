object FileFormatSaveAsDialog: TFileFormatSaveAsDialog
  Caption = 'Save File Format As'
  ClientHeight = 68
  ClientWidth = 313
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object Edit: TUiComboBox
    Left = 8
    Top = 8
    Width = 297
    Height = 21
    AutoComplete = False
    TabOrder = 0
    OnChange = EditChange
    OnClick = EditClick
    OnKeyDown = EditKeyDown
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 29
    Width = 313
    TabOrder = 1
    object OkBtn: TUiOkBtn
      OnClick = OkClick
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
