object DirScriptDialog: TDirScriptDialog
  BorderIcons = [biSystemMenu, biMinimize, biMaximize]
  BorderStyle = bsSizeable
  Caption = '%'
  ClientHeight = 319
  ClientWidth = 433
  Constraints.MinHeight = 215
  Constraints.MinWidth = 185
  OnClose = FormClose
  OnCloseQuery = FormCloseQuery
  OnCreate = FormCreate
  OnShortCut = FormShortCut
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object IconShape: TShape
    Left = 8
    Top = 8
    Width = 48
    Height = 48
    Pen.Color = clSilver
    Pen.Width = 4
  end
  object Image: TUiDlgIcon
    Left = 16
    Top = 16
    IconType = diApplication
  end
  object ProgressLbl: TUiLabel
    Left = 72
    Top = 16
    Height = 13
    Caption = '%'
  end
  object ProgressBar: TUiProgressBar
    Left = 72
    Top = 35
    Width = 349
    Height = 17
    Anchors = [akLeft, akTop, akRight]
    TabOrder = 0
    Visible = False
  end
  object PageControl: TUiPageControl
    Left = 8
    Top = 61
    Width = 417
    Height = 173
    ActivePage = LogTabSheet
    Anchors = [akLeft, akTop, akRight, akBottom]
    TabOrder = 1
    object LogTabSheet: TUiTabSheet
      Caption = 'Log'
      object LogFrame: TLogFrame
        Left = 0
        Top = 0
        Width = 409
        Height = 145
        Align = alClient
        PopupMenu = LogPopup
        TabOrder = 0
        object LeftPanel: TUiPanel
          Height = 145
        end
        object ListBox: TUiVirtualListBox
          Width = 388
          Height = 145
          PopupMenu = LogPopup
          TabStop = True
        end
      end
    end
    object ScriptTabSheet: TUiTabSheet
      Caption = 'Script'
      object ScriptListBox: TUiListBox
        Left = 0
        Top = 0
        Width = 409
        Height = 145
        Align = alClient
        TabOrder = 0
      end
    end
    object ErrorLogTabSheet: TUiTabSheet
      Caption = 'Errors'
      object ErrorLogListBox: TUiListBox
        Left = 0
        Top = 0
        Width = 409
        Height = 145
        Align = alClient
        TabOrder = 0
      end
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 234
    Width = 433
    Height = 85
    TabOrder = 2
    SizeGripper = True
    ItemTabOrder0 = False
    ItemTop = 54
    object BeepWhenFinishedEdit: TUiCheckBox
      Left = 8
      Top = 8
      Height = 17
      Caption = '&Beep when finished'
      TabOrder = 0
    end
    object CloseWhenFinishedEdit: TUiCheckBox
      Left = 8
      Top = 29
      Height = 17
      Caption = '&Close when finished'
      TabOrder = 1
    end
    object CancelBtn: TUiCancelBtn
      OnClick = CancelClick
    end
    object CloseBtn: TUiCloseBtn
    end
  end
  object LogPopup: TUiPopupMenu
    Left = 8
    Top = 8
    object LogCopyItem: TUiMenuItem
      Caption = 'Copy'
      ShortCut = 16451
      OnClick = LogCopyClick
    end
    object LogSelectAllItem: TUiMenuItem
      Caption = 'Select All'
      ShortCut = 16449
      OnClick = LogSelectAllClick
    end
  end
end
