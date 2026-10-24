object BrowseMachineDialog: TBrowseMachineDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgBrowseMachine'
  BorderIcons = [biSystemMenu, biHelp]
  BorderStyle = bsSizeable
  Caption = 'Select Computer'
  ClientHeight = 215
  ClientWidth = 313
  Constraints.MinHeight = 104
  Constraints.MinWidth = 185
  OnCloseQuery = FormCloseQuery
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object ListBox: TUiListBox
    Left = 8
    Top = 8
    Width = 297
    Height = 168
    Anchors = [akLeft, akTop, akRight, akBottom]
    TabOrder = 0
    OnClick = ListBoxClick
    OnDblClick = ListBoxDblClick
    OnKeyDown = ListBoxKeyDown
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 176
    Width = 313
    TabOrder = 1
    SizeGripper = True
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
