object ProfileSaveAsDialog: TProfileSaveAsDialog
  BorderStyle = bsSizeable
  Caption = 'Save Profile As'
  ClientHeight = 186
  ClientWidth = 313
  Constraints.MinHeight = 166
  Constraints.MinWidth = 303
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object EditLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = '&Save current settings as:'
    FocusControl = Edit
  end
  object TreeViewLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = '&Create in:'
    FocusControl = TreeView
  end
  object Edit: TUiComboBox
    Left = 8
    Top = 25
    Width = 297
    Height = 21
    AutoComplete = False
    Anchors = [akLeft, akTop, akRight]
    TabOrder = 0
    OnChange = EditChange
    OnClick = EditClick
    OnKeyDown = EditKeyDown
    OnKeyPress = EditKeyPress
  end
  object TreeView: TUiTreeView
    Left = 8
    Top = 71
    Width = 297
    Height = 76
    Anchors = [akLeft, akTop, akRight, akBottom]
    Images = BcImages.MainImages
    PopupMenu = TreePopup
    TabOrder = 1
    OnCancelEdit = TreeViewCancelEdit
    OnChange = TreeViewChange
    OnEdited = TreeViewEdited
    OnEditing = TreeViewEditing
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 147
    Width = 313
    TabOrder = 2
    SizeGripper = True
    ItemTabOrder0 = False
    object NewSubfolderBtn: TUiBitBtn
      Left = 8
      Top = 8
      Caption = '&New Subfolder'
      ImageIndex = imgNewSessionFolder
      Images = BcImages.MainImages
      TabOrder = 0
      OnClick = NewSubfolderClick
      AutoSize = asLeft
    end
    object OkBtn: TUiOkBtn
      OnClick = OkClick
    end
    object CancelBtn: TUiCancelBtn
    end
  end
  object TreePopup: TUiPopupMenu
    Left = 8
    Top = 8
    object NewSubfolderItem: TUiMenuItem
      Caption = 'New Subfolder'
      ShortCut = 45
      OnClick = NewSubfolderClick
    end
    object DeleteItem: TUiMenuItem
      Caption = 'Delete'
      ShortCut = 46
      OnClick = DeleteClick
    end
    object RenameItem: TUiMenuItem
      Caption = 'Rename'
      ShortCut = 113
      OnClick = RenameClick
    end
  end
end
