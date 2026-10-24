object WorkspaceSaveAsDialog: TWorkspaceSaveAsDialog
  Caption = 'Save Workspace As'
  ClientHeight = 85
  ClientWidth = 313
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object EditLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = '&Save current view configuration as:'
    FocusControl = Edit
  end
  object Edit: TUiComboBox
    Left = 8
    Top = 25
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
    Top = 46
    Width = 313
    TabOrder = 1
    object OkBtn: TUiOkBtn
      OnClick = OkClick
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
